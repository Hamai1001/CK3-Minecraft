package dev.ckcraft;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Every network operation runs on a worker; never block the game tick. */
public final class BridgeClient implements AutoCloseable {
    private final Path config;
    private final ExecutorService worker = Executors.newSingleThreadExecutor(r -> {
        Thread thread = new Thread(r, "ckcraft-bridge");
        thread.setDaemon(true);
        return thread;
    });
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
    private final Gson gson = new Gson();

    public BridgeClient(Path config) { this.config = config; }

    public CompletableFuture<JsonObject> get() { return call("/v1/session", null); }
    public CompletableFuture<JsonObject> post(String endpoint, JsonObject body) { return call(endpoint, body); }

    private CompletableFuture<JsonObject> call(String endpoint, JsonObject body) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                JsonObject connection = gson.fromJson(Files.readString(config), JsonObject.class);
                int port = connection.get("port").getAsInt();
                String token = connection.get("token").getAsString();
                if (connection.get("protocol").getAsInt() != 1 || !connection.get("host").getAsString().equals("127.0.0.1")
                        || port < 1 || port > 65535 || !token.matches("[A-Za-z0-9_-]{32,128}")) {
                    throw new IOException("Invalid private bridge configuration");
                }
                HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + endpoint))
                        .timeout(Duration.ofSeconds(4)).header("Authorization", "Bearer " + token);
                if (body == null) builder.GET();
                else builder.header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(gson.toJson(body)));
                HttpResponse<String> response = http.send(builder.build(), HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() != 200 || response.body().length() > 32768) {
                    throw new IOException("Bridge rejected request: HTTP " + response.statusCode());
                }
                JsonObject result = gson.fromJson(response.body(), JsonObject.class);
                if (result.get("protocol").getAsInt() != 1) throw new IOException("Protocol version mismatch");
                return result;
            } catch (Exception error) {
                if (error instanceof InterruptedException) Thread.currentThread().interrupt();
                throw new java.util.concurrent.CompletionException(error);
            }
        }, worker);
    }

    public void close() { worker.shutdownNow(); }
}
