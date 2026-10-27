using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Mono.Cecil;
using Mono.Cecil.Cil;

// Offline metadata inspection only; target assemblies are never executed.
if (args.Length != 2) {
    Console.Error.WriteLine("usage: MenuOptimizationProbe <menu DLL> <System DLL>");
    return 2;
}
void Check(bool condition, string message) {
    if (!condition) throw new InvalidDataException(message);
}
void Hash(string path, string expected) {
    var actual = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
    Check(actual == expected, "Unexpected input: " + path);
    Console.WriteLine($"SHA256 {Path.GetFileName(path)} {actual}");
}
Hash(args[0], "f2a5c1daaa515330503800d39d6025267615dff20f6bf78d8ef67d0e4c0c1921");
Hash(args[1], "72056f70facd6433bd696de41ba857c387c22abfdeaa6032d39f0a640acc9065");
using var menu = ModuleDefinition.ReadModule(args[0]);
using var system = ModuleDefinition.ReadModule(args[1]);
MethodDefinition Method(ModuleDefinition module, uint token) {
    var method = module.LookupToken(new MetadataToken(token)) as MethodDefinition;
    Check(method != null && method.HasBody, "Missing method/body " + token.ToString("x8"));
    Console.WriteLine($"\nMETHOD {module.Name} 0x{token:x8} {method.FullName}");
    foreach (var instruction in method.Body.Instructions)
        Console.WriteLine($"IL {instruction.Offset:x4} {instruction}");
    return method;
}
Instruction At(MethodDefinition method, int offset) => method.Body.Instructions.Single(i => i.Offset == offset);
var views = Method(menu, 0x06000baa);
var buttons = Method(menu, 0x06000bab);
var now = Method(menu, 0x06001211);
var after = Method(menu, 0x06001212);
Check(views.Name == "CreateViews" && buttons.Name == "SetButtonsInfo", "Unexpected UI tokens");
Check(views.Body.Instructions.Any(i => i.OpCode == OpCodes.Ldstr && (string)i.Operand == "30"), "Missing default duration text");
Check(views.Body.Instructions.Any(i => i.OpCode == OpCodes.Ldstr && (string)i.Operand == "60"), "Missing alternate duration text");
Check(At(views, 0x0d).Operand is int key && key == 1163, "Unexpected system-info key");
Check(At(views, 0x12).Operand is MethodReference get && get.Name == "GetInt", "Unexpected system-info getter");
Check(At(views, 0x4f).Operand is sbyte model && model == 37, "Unexpected selector constant");
Check(At(views, 0x51).OpCode.Code == Code.Bne_Un_S && ((Instruction)At(views, 0x51).Operand).Offset == 0x59, "Unexpected duration branch");
Check(At(buttons, 0x1f).Operand is MethodReference nowHandler && nowHandler.MetadataToken.ToUInt32() == 0x06001211, "Unexpected first button binding");
Check(At(buttons, 0x5d).Operand is MethodReference afterHandler && afterHandler.MetadataToken.ToUInt32() == 0x06001212, "Unexpected second button binding");
foreach (var pair in new[] { (method: now, code: Code.Ldc_I4_0), (method: after, code: Code.Ldc_I4_1) }) {
    Check(At(pair.method, 0x66).OpCode.Code == pair.code, "Unexpected mode literal");
    Check(At(pair.method, 0x67).Operand is MethodReference call && call.Name == "QDDisplayRequestELSensing", "Unexpected mode consumer");
}
Check(At(after, 0x86).Operand is int toast && toast == 3000, "Unexpected toast argument");
Check(At(after, 0x8b).Operand is MethodReference toastFactory && toastFactory.Name == "GetMenuCommonToastPopupAttributes", "Unexpected toast consumer");
var bridge = Method(system, 0x060000b2);
Check(At(bridge, 0x1e).OpCode.Code == Code.Ldarg_0, "Bridge no longer forwards its argument");
Check(At(bridge, 0x1f).Operand is MethodReference native && native.Name == "qd_display_request_el_sensing", "Unexpected bridge");
var import = system.GetTypes().SelectMany(t => t.Methods)
    .Single(m => m.Name == "qd_display_request_el_sensing" && m.IsPInvokeImpl);
Console.WriteLine($"PINVOKE 0x{import.MetadataToken.ToInt32():x8} {import.FullName} module={import.PInvokeInfo.Module.Name} entry={import.PInvokeInfo.EntryPoint}");
Check(import.PInvokeInfo.EntryPoint == "qd_display_request_el_sensing", "Unexpected native entrypoint");
Check(import.PInvokeInfo.Module.Name == "/usr/lib/libdeviced.so.1", "Unexpected native module");
Console.WriteLine("PASS: bounded metadata/argument checks; UI execution and popup identity unproven.");
return 0;
