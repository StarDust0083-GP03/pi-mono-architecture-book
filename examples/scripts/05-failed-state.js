store("inspected", 999);
await tools.write({ path: "disposable.txt", content: "文件写入不会因脚本报错而自动回滚" });
throw new Error("模拟脚本失败");
