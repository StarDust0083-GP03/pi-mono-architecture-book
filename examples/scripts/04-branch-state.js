const count = (load("inspected") ?? 0) + 1;
store("inspected", count);
text({ count });
