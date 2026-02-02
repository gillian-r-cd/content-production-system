// web/tailwind.config.js
// TailwindCSS配置
// 功能：定义颜色、主题、插件

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色调（来自ui_design.md）
        primary: {
          DEFAULT: "#1a73e8",
          foreground: "#ffffff",
        },
        success: {
          DEFAULT: "#34a853",
          foreground: "#ffffff",
        },
        warning: {
          DEFAULT: "#fbbc05",
          foreground: "#202124",
        },
        error: {
          DEFAULT: "#ea4335",
          foreground: "#ffffff",
        },
        neutral: {
          DEFAULT: "#5f6368",
        },
        // 背景色
        background: {
          DEFAULT: "#ffffff",
          secondary: "#f8f9fa",
          tertiary: "#e8eaed",
        },
        // 文字色
        foreground: {
          DEFAULT: "#202124",
          secondary: "#5f6368",
          disabled: "#9aa0a6",
        },
        // Shadcn/ui需要的
        border: "#e8eaed",
        input: "#e8eaed",
        ring: "#1a73e8",
        muted: {
          DEFAULT: "#f8f9fa",
          foreground: "#5f6368",
        },
        accent: {
          DEFAULT: "#f8f9fa",
          foreground: "#202124",
        },
        card: {
          DEFAULT: "#ffffff",
          foreground: "#202124",
        },
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [],
}



