using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Text.Json;

internal static class Program
{
    private static string Blob(MetadataReader metadata, BlobHandle handle) =>
        Convert.ToHexString(metadata.GetBlobBytes(handle)).ToLowerInvariant();

    private static int Main(string[] args)
    {
        if (args.Length == 0) return 63;
        List<object> files = new();
        foreach (string path in args)
        {
            using FileStream stream = File.OpenRead(path);
            using PEReader pe = new(stream);
            MetadataReader metadata = pe.GetMetadataReader();
            AssemblyDefinition own = metadata.GetAssemblyDefinition();
            List<object> references = new();
            foreach (AssemblyReferenceHandle handle in metadata.AssemblyReferences.OrderBy(
                         value => metadata.GetString(metadata.GetAssemblyReference(value).Name),
                         StringComparer.Ordinal))
            {
                AssemblyReference item = metadata.GetAssemblyReference(handle);
                references.Add(new
                {
                    name = metadata.GetString(item.Name),
                    version = item.Version.ToString(),
                    culture = item.Culture.IsNil ? "" : metadata.GetString(item.Culture),
                    public_key_or_token = Blob(metadata, item.PublicKeyOrToken),
                    flags = item.Flags.ToString()
                });
            }
            List<string> modules = new();
            int moduleCount = metadata.GetTableRowCount(TableIndex.ModuleRef);
            for (int row = 1; row <= moduleCount; row++)
            {
                ModuleReference item = metadata.GetModuleReference(
                    MetadataTokens.ModuleReferenceHandle(row));
                modules.Add(metadata.GetString(item.Name));
            }
            modules.Sort(StringComparer.Ordinal);
            files.Add(new
            {
                file = Path.GetFileName(path),
                assembly = metadata.GetString(own.Name),
                version = own.Version.ToString(),
                assembly_references = references,
                native_module_references = modules
            });
        }
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            schema = "managed-ui-tab-dependency-closure-v1",
            files
        }, new JsonSerializerOptions { WriteIndented = true }));
        return 0;
    }
}
