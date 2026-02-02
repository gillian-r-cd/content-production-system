// web/src/lib/utils.ts
// 工具函数
// 功能：className合并、格式化等

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}



