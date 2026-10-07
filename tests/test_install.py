from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from install_ck3 import install


class InstallTests(unittest.TestCase):
    def test_repeat_install_preserves_user_saves_and_protects_mod_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs=Path(tmp)
            save=docs/'Paradox Interactive'/'Crusader Kings III'/'save games'/'untouched.ck3'
            save.parent.mkdir(parents=True); save.write_text('original-save')
            target=install(docs)
            self.assertEqual(install(docs),target)
            self.assertEqual(save.read_text(),'original-save')
            events=target/'events'/'ckcraft_events.txt'
            events.write_text('user edits')
            with self.assertRaises(RuntimeError): install(docs)
            self.assertEqual(events.read_text(),'user edits')

    def test_unrelated_mod_folder_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs=Path(tmp)
            target=docs/'Paradox Interactive'/'Crusader Kings III'/'mod'/'ckcraft_dev'
            target.mkdir(parents=True); existing=target/'user.txt'; existing.write_text('keep')
            with self.assertRaises(RuntimeError): install(docs)
            self.assertEqual(existing.read_text(),'keep')
