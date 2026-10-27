using System.Text.Json;
Console.WriteLine(JsonSerializer.Serialize(new { status=File.ReadAllText("/proc/self/status"), label=File.ReadAllText("/proc/self/attr/current") }));
