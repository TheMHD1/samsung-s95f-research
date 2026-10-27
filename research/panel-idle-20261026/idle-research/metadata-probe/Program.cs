using System;
using System.Linq;
using Mono.Cecil;

if (args.Length != 1)
{
    Console.Error.WriteLine("usage: MetadataProbe <assembly>");
    Environment.Exit(2);
}

using var module = ModuleDefinition.ReadModule(args[0]);
foreach (var reference in module.AssemblyReferences.OrderBy(x => x.Name))
    Console.WriteLine($"AssemblyRef\t{reference.Name}\t{reference.Version}\t{reference.PublicKeyToken}");

foreach (var type in module.GetTypeReferences()
    .Where(x => x.Namespace == "Tizen.TV.System.Avoc" || x.FullName.Contains("Avocd"))
    .OrderBy(x => x.FullName))
    Console.WriteLine($"TypeRef\t{type.FullName}\tScope={type.Scope}");

foreach (var type in module.GetTypes()
    .Where(x => x.Namespace == "Tizen.TV.System.Avoc" || x.FullName.Contains("Avocd"))
    .OrderBy(x => x.FullName))
{
    Console.WriteLine($"TypeDef\t{type.FullName}");
    foreach (var method in type.Methods.Where(x => x.Name.Contains("NewHome") || x.Name.Contains("PanelMute")))
    {
        Console.WriteLine($"MethodDef\t0x{method.MetadataToken.ToInt32():x8}\t{method.FullName}\tPInvoke={method.IsPInvokeImpl}");
        if (method.HasBody)
            foreach (var instruction in method.Body.Instructions)
                Console.WriteLine($"IL\t{instruction.Offset:x4}\t{instruction}");
    }
}

foreach (var type in module.GetTypes().Where(x => x.FullName == "Interop/Avocd"))
foreach (var method in type.Methods.Where(x => x.Name.Contains("new_home")))
{
    Console.WriteLine($"Interop\t0x{method.MetadataToken.ToInt32():x8}\t{method.FullName}\tPInvoke={method.PInvokeInfo?.Module?.Name}\tEntry={method.PInvokeInfo?.EntryPoint}");
}
