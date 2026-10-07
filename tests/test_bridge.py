from pathlib import Path
import json
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"bridge"))
sys.path.insert(0,str(ROOT/"tools"))
from ckcraft.protocol import parse_line, Request, Ack
from ckcraft.state import State, Conflict
from ckcraft.server import make_server
from ckcraft.log_reader import LogReader
import design

FRAME = "[debug] CKCRAFT1|REQUEST|travel_duel|42|1|12|83|18|101|Adelheid|Otto\n"


class ProtocolTests(unittest.TestCase):
    def test_actual_character_data_is_preserved(self):
        request = parse_line(FRAME)
        self.assertEqual((request.character,request.prowess,request.opponent,request.opponent_prowess,request.province),(42,12,83,18,101))
        self.assertEqual(request.name,"Adelheid")

    def test_fixed_point_engine_numbers_are_accepted(self):
        self.assertEqual(parse_line(FRAME.replace("|1|12|","|1.000|12.000|")).sequence,1)

    def test_incomplete_live_ck3_export_is_diagnosed_without_fabricating_data(self):
        frame = "CKCRAFT1|REQUEST|free_travel||||0|0|||none"
        with self.assertRaisesRegex(ValueError, r"empty: character, sequence, prowess, province, name"):
            parse_line(frame)

    def test_unresolved_localization_and_script_injection_are_rejected(self):
        for replacement in ["[ROOT.Char.GetID]","42 } add_gold = 999","NaN","Infinity","-1","42.5"]:
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                parse_line(FRAME.replace("|42|","|"+replacement+"|"))

    def test_a_real_distinct_opponent_is_required(self):
        for value in ["0","42"]:
            with self.assertRaises(ValueError): parse_line(FRAME.replace("|83|","|"+value+"|"))

    def test_noise_ignored_but_malformed_frames_fail(self):
        self.assertIsNone(parse_line("[debug] normal engine message"))
        for frame in [FRAME.replace("travel_duel","unknown"),FRAME+"|extra",FRAME.replace("Adelheid",""),FRAME.replace("Adelheid","Bad|Name")]:
            with self.assertRaises(ValueError): parse_line(frame)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = State(self.root,"test-campaign",ROOT/"design"/"sheets")
        self.request = parse_line(FRAME)
        self.key = self.request.identity("test-campaign")

    def tearDown(self):
        self.state.close(); self.temp.cleanup()

    def claim(self):
        self.state.accept(self.request)
        self.state.claim(self.key,"player-a","instance-a")

    def test_result_is_not_complete_until_exact_ck3_ack(self):
        self.claim()
        self.state.result(self.key,"player-a","instance-a","won")
        self.assertEqual(self.state.snapshot()["session"]["status"],"RETURN_PENDING")
        command = json.loads((self.root/"return-command.json").read_text())["command"]
        self.assertIn("var:ckcraft_sequence = 1",command)
        self.assertIn("has_character_flag = ckcraft_pending",command)
        self.assertIn("id = ckcraft.2001",command)
        self.assertFalse(self.state.acknowledge(Ack(42,2,"won")))
        self.assertFalse(self.state.acknowledge(Ack(83,1,"won")))
        self.assertFalse(self.state.acknowledge(Ack(42,1,"lost")))
        self.assertTrue(self.state.acknowledge(Ack(42,1,"won")))
        self.assertIsNone(self.state.snapshot()["session"])
        self.assertFalse((self.root/"return-command.json").exists())

    def test_replay_cannot_award_twice(self):
        self.claim()
        self.state.result(self.key,"player-a","instance-a","won")
        self.state.result(self.key,"player-a","instance-a","won")
        self.state.acknowledge(Ack(42,1,"won"))
        self.assertFalse(self.state.accept(self.request))
        self.assertFalse(self.state.acknowledge(Ack(42,1,"won")))

    def test_second_instance_cannot_claim_or_report_result(self):
        self.claim()
        with self.assertRaises(Conflict): self.state.claim(self.key,"player-a","instance-b")
        with self.assertRaises(Conflict): self.state.result(self.key,"player-b","instance-a","won")
        with self.assertRaises(Conflict): self.state.result(self.key,"player-a","instance-b","won")

    def test_early_and_invalid_results_are_rejected(self):
        self.state.accept(self.request)
        with self.assertRaises(Conflict): self.state.result(self.key,"player-a","instance-a","won")
        self.state.claim(self.key,"player-a","instance-a")
        with self.assertRaises(Conflict): self.state.result(self.key,"player-a","instance-a","travelled")
        with self.assertRaises(Conflict): self.state.result(self.key,"player-a","instance-a","add_gold")

    def test_pending_event_survives_restart(self):
        self.claim()
        self.state.result(self.key,"player-a","instance-a","lost")
        self.state.close()
        self.state = State(self.root,"test-campaign",ROOT/"design"/"sheets")
        self.assertEqual(self.state.snapshot()["session"]["outcome"],"lost")
        self.assertTrue(self.state.acknowledge(Ack(42,1,"lost")))

    def test_new_event_does_not_overwrite_old_event(self):
        self.state.accept(self.request)
        with self.assertRaises(Conflict): self.state.accept(parse_line(FRAME.replace("|1|12|","|2|12|")))

    def test_sequence_reuse_with_different_content_fails(self):
        self.state.accept(self.request)
        with self.assertRaises(Conflict): self.state.accept(parse_line(FRAME.replace("|12|","|13|")))

    def test_free_travel_has_its_own_valid_outcomes(self):
        request = parse_line("CKCRAFT1|REQUEST|free_travel|42|2|12|0|0|101|Adelheid|none")
        key = request.identity("test-campaign")
        self.state.accept(request)
        self.state.claim(key,"player-a","instance-a")
        with self.assertRaises(Conflict): self.state.result(key,"player-a","instance-a","won")
        self.state.result(key,"player-a","instance-a","travelled")
        self.assertTrue(self.state.acknowledge(Ack(42,2,"travelled")))

    def test_ck3_cancellation_releases_waiting_and_active_sessions(self):
        self.state.accept(self.request)
        self.assertTrue(self.state.acknowledge(Ack(42,1,"aborted")))
        request=parse_line(FRAME.replace('|1|12|','|2|12|'))
        key=request.identity('test-campaign')
        self.state.accept(request)
        self.state.claim(key,'player-a','instance-a')
        self.assertTrue(self.state.acknowledge(Ack(42,2,'aborted')))
        self.assertIsNone(self.state.result(key,'player-a','instance-a','won')['session'])
        self.assertFalse((self.root/'return-command.json').exists())


class LogTests(unittest.TestCase):
    def test_existing_log_is_not_replayed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"debug.log"; path.write_text(FRAME)
            tail=LogReader(path)
            self.assertEqual(tail.read(),[])
            with path.open("a") as stream: stream.write(FRAME)
            self.assertEqual(tail.read(),[FRAME.rstrip("\n")])

    def test_newly_created_log_and_partial_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"debug.log"; tail=LogReader(path)
            self.assertEqual(tail.read(),[])
            path.write_text(FRAME[:20]); self.assertEqual(tail.read(),[])
            with path.open("a") as stream: stream.write(FRAME[20:])
            self.assertEqual(tail.read(),[FRAME.rstrip("\n")])

    def test_replaced_log_and_truncation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"debug.log"; path.write_text("historical\n"*100)
            tail=LogReader(path); tail.read()
            path.write_text(FRAME)
            self.assertEqual(tail.read(),[FRAME.rstrip("\n")])
            path.rename(path.with_suffix(".old")); path.write_text(FRAME)
            self.assertEqual(tail.read(),[FRAME.rstrip("\n")])


class HttpIntegrationTests(unittest.TestCase):
    """Real HTTP/socket transport with synthetic CK3 frames; not a game test."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.state=State(Path(self.temp.name),"http-test",ROOT/"design"/"sheets")
        self.server=make_server(self.state,"test-token")
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.state.close(); self.temp.cleanup()

    def http(self,path,body=None,token="test-token",headers=None):
        h={"Authorization":"Bearer "+token,"Content-Type":"application/json",**(headers or {})}
        req=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
        try:
            with urllib.request.urlopen(req,timeout=3) as r: return r.status,json.load(r)
        except urllib.error.HTTPError as error: return error.code,json.load(error)

    def test_full_roundtrip_is_completed_only_after_log_ack(self):
        self.state.accept(parse_line(FRAME))
        code,data=self.http("/v1/session")
        self.assertEqual(code,200)
        key=data["session"]["id"]
        claim={"session":key,"player":"local-player","instance":"local-instance"}
        self.assertEqual(self.http("/v1/claim",claim)[0],200)
        code,data=self.http("/v1/result",{**claim,"outcome":"won"})
        self.assertEqual((code,data["session"]["status"]),(200,"RETURN_PENDING"))
        self.state.acknowledge(parse_line("[debug] CKCRAFT1|ACK|42|1|won"))
        self.assertIsNone(self.http("/v1/session")[1]["session"])

    def test_auth_origin_and_dns_rebinding_protection(self):
        self.assertEqual(self.http("/v1/session",token="wrong")[0],401)
        self.assertEqual(self.http("/v1/session",token="é")[0],401)
        self.assertEqual(self.http("/v1/session",headers={"Origin":"https://example.com"})[0],403)
        self.assertEqual(self.http("/v1/session",headers={"Host":"evil.example"})[0],403)

    def test_invalid_body_fails_without_mutating_state(self):
        for body in [{},[],{"session":"x","player":"p","instance":"i","outcome":"won","extra":1}]:
            self.assertEqual(self.http("/v1/result",body)[0],400)
        self.assertIsNone(self.state.snapshot()["session"])


class DesignTests(unittest.TestCase):
    def test_debug_export_is_independent_of_event_localization_context(self):
        tables = design.load()
        files = design.generate(tables)
        events = files["ck3/ckcraft/events/ckcraft_events.txt"]
        # The selected, real NPC must survive the loss of debug_log's event
        # localization context. Store before exporting; clear after every ACK.
        self.assertLess(events.index("set_variable = { name = ckcraft_opponent value = scope:ckcraft_opponent }"),
                        events.index("debug_log = ckcraft_request_travel_duel"))
        for row in tables["outcomes"]["rows"]:
            body = events.split(row["ck3_event"] + " = {", 1)[1].split("\n}\n", 1)[0]
            self.assertLess(body.index("debug_log = ckcraft_ack_"), body.index("remove_variable = ckcraft_opponent"))
        for lang in ["german", "english"]:
            loc = files[f"ck3/ckcraft/localization/{lang}/ckcraft_l_{lang}.yml"]
            wire_lines = [line for line in loc.splitlines() if '"CKCRAFT1|' in line]
            self.assertEqual(len(wire_lines), len(tables["scenarios"]["rows"]) + len(tables["outcomes"]["rows"]))
            for line in wire_lines:
                self.assertNotIn("ROOT.", line)
                self.assertNotIn("SCOPE.", line)
                self.assertIn("[GetPlayer.GetID]", line)
                self.assertIn("[GetPlayer.MakeScope.Var('ckcraft_sequence').GetValue]", line)
            duel = next(line for line in wire_lines if "|travel_duel|" in line)
            self.assertIn("[GetPlayer.MakeScope.Var('ckcraft_opponent').Char.GetID]", duel)
            self.assertIn("[GetPlayer.MakeScope.Var('ckcraft_opponent').Char.GetProwess]", duel)

    def test_missing_cells_and_dangling_refs_block_preflight(self):
        tables=design.load()
        del tables["scenarios"]["rows"][0]["radius"]
        tables["scenarios"]["rows"][1]["enemy"]="missing_enemy"
        errors=design.preflight(tables)
        self.assertTrue(any("unfilled cell" in e for e in errors))
        self.assertTrue(any("unresolved reference" in e for e in errors))

    def test_unsafe_event_id_and_missing_implementation_block_preflight(self):
        tables=design.load()
        tables["outcomes"]["rows"][0]["ck3_event"]="x } add_gold = 999"
        tables["systems"]["rows"][0]["implementation"]="missing.py"
        errors=design.preflight(tables)
        self.assertTrue(any("unsafe event ID" in e for e in errors))
        self.assertTrue(any("implementation missing" in e for e in errors))

    def test_every_generated_row_and_ck3_ack_matches_its_table(self):
        tables=design.load()
        self.assertEqual(design.preflight(tables),[])
        files=design.generate(tables)
        for path,text in files.items():
            self.assertEqual((ROOT/path).read_text(encoding="utf-8"),text,path)
        java=files["minecraft/src/main/java/dev/ckcraft/GeneratedDesign.java"]
        for table,cls in design.CLASSES.items():
            self.assertEqual(java.count("new "+cls+"("),len(tables[table]["rows"]))


if __name__ == '__main__':
    unittest.main()
