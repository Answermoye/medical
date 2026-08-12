# 🎨 MedicalGuide 设计系统

## 设计方向：「温润的清晰度」

> 温暖、可信赖、有机、流动

---

## 🎨 调色板

### 核心色彩

| 角色 | 色值 | 名称 | 用途 |
|------|------|------|------|
| Primary | `#2D3047` | 深靛蓝 | 主要文字、导航、品牌 |
| Primary Light | `#3D4060` | 浅靛蓝 | 悬停状态、次要元素 |
| Primary Dark | `#1A1A2E` | 深夜蓝 | 侧边栏背景、深色区域 |
| Accent | `#D4A373` | 温暖琥珀 | 强调、CTA、活跃状态 |
| Accent Light | `#E8C9A0` | 浅琥珀 | 悬停状态、边框 |
| Accent Dark | `#B8864E` | 深琥珀 | 文字链接、强调文字 |

### 背景色系

| 色值 | 名称 | 用途 |
|------|------|------|
| `#FFFCF7` | 暖米白 | 页面主背景 |
| `#FEF9F0` | 奶油白 | 卡片、面板背景 |
| `#FEFCE8` | 浅奶油 | 悬停状态、高亮区域 |
| `rgba(45, 48, 71, 0.03)` | 半透明覆盖 | 微妙的层次感 |

### 功能色

| 角色 | 色值 | 用途 |
|------|------|------|
| Success | `#6B8F71` | 鼠尾草绿 - 成功、确认、批准 |
| Warning | `#E8985E` | 暖橙 - 警告、待处理 |
| Danger | `#C75C5C` | 砖红 - 错误、危险、驳回 |
| Info | `#5B8DB8` | 天蓝 - 信息、提示 |

---

## 📝 字体系统

### 字体选择

| 角色 | 字体 | 备选 | 用途 |
|------|------|------|------|
| Display | **Fraunces** | Georgia, serif | 标题、品牌、强调 |
| Body | **Source Sans 3** | -apple-system, sans-serif | 正文、UI、按钮 |
| Mono | **JetBrains Mono** | Fira Code, monospace | 代码、数据 |

### 字体大小（模块化比例 1.25）

| 名称 | 大小 | 用途 |
|------|------|------|
| `--text-xs` | 0.75rem (12px) | 标签、辅助文字 |
| `--text-sm` | 0.875rem (14px) | 次要文字、按钮 |
| `--text-base` | 1rem (16px) | 正文 |
| `--text-lg` | 1.125rem (18px) | 小标题 |
| `--text-xl` | 1.25rem (20px) | 卡片标题 |
| `--text-2xl` | 1.5rem (24px) | 页面标题 |
| `--text-3xl` | 1.875rem (30px) | 大标题 |
| `--text-4xl` | 2.25rem (36px) | 英雄区标题 |
| `--text-5xl` | 3rem (48px) | 超大标题 |

---

## 📐 间距系统

### 基础间距

| 变量 | 大小 | 用途 |
|------|------|------|
| `--space-1` | 4px | 微间距 |
| `--space-2` | 8px | 小间距 |
| `--space-3` | 12px | 中小间距 |
| `--space-4` | 16px | 中间距 |
| `--space-5` | 20px | 中大间距 |
| `--space-6` | 24px | 大间距 |
| `--space-8` | 32px | 超大间距 |
| `--space-10` | 40px | 巨大间距 |
| `--space-12` | 48px | 超巨大间距 |
| `--space-16` | 64px | 极大间距 |

---

## 🎭 圆角系统

### 有机曲线

| 变量 | 大小 | 用途 |
|------|------|------|
| `--radius-sm` | 8px | 小元素、标签 |
| `--radius-md` | 12px | 按钮、输入框 |
| `--radius-lg` | 16px | 卡片、面板 |
| `--radius-xl` | 20px | 大卡片、对话框 |
| `--radius-2xl` | 24px | 页面级容器 |
| `--radius-3xl` | 32px | 特殊装饰 |
| `--radius-full` | 9999px | 圆形、胶囊 |

---

## 🌟 阴影系统

### 柔和温暖阴影

| 变量 | 效果 | 用途 |
|------|------|------|
| `--shadow-xs` | 0 1px 2px rgba(26, 26, 46, 0.04) | 微妙层次 |
| `--shadow-sm` | 0 2px 8px rgba(26, 26, 46, 0.06) | 卡片、按钮 |
| `--shadow-md` | 0 4px 16px rgba(26, 26, 46, 0.08) | 悬停状态 |
| `--shadow-lg` | 0 8px 32px rgba(26, 26, 46, 0.10) | 弹出层 |
| `--shadow-xl` | 0 16px 48px rgba(26, 26, 46, 0.12) | 对话框 |

---

## 🎨 渐变系统

### 品牌渐变

```css
--gradient-accent: linear-gradient(135deg, #D4A373 0%, #E8C9A0 100%);
--gradient-primary: linear-gradient(135deg, #2D3047 0%, #3D4060 100%);
--gradient-warm: linear-gradient(135deg, #FFFCF7 0%, #FEF9F0 100%);
--gradient-glow: linear-gradient(135deg, rgba(212, 163, 115, 0.2) 0%, rgba(232, 201, 160, 0.1) 100%);
```

---

## 🎭 动画系统

### 过渡动画

```css
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-bounce: 500ms cubic-bezier(0.34, 1.56, 0.64, 1);
```

### 关键帧动画

- **breathe** - 呼吸动画（AI 处理中状态）
- **pulse-glow** - 脉冲发光（活跃状态）
- **float** - 漂浮动画（装饰元素）
- **gradient-shift** - 渐变流动（签名卡片）

---

## 🃏 组件设计

### 呼吸卡片（Breathing Card）

签名设计元素，具有以下特性：

1. **渐变边框** - 悬停时显示从透明到琥珀色的渐变边框
2. **上浮效果** - 悬停时卡片轻微上移
3. **脉冲发光** - AI 处理中时显示呼吸光效
4. **有机圆角** - 使用 `--radius-xl` 或更大

```css
.breathing-card {
  position: relative;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  transition: all var(--transition-normal);
  border: 1px solid var(--color-border-light);
}

.breathing-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

---

## 📱 响应式设计

### 断点

- **768px** - 移动端
- **1024px** - 平板端
- **1200px** - 桌面端

### 适配策略

1. **侧边栏** - 移动端隐藏，通过菜单触发
2. **网格布局** - 使用 `auto-fill` 和 `minmax`
3. **间距调整** - 移动端减少间距
4. **字体大小** - 移动端适当缩小

---

## ♿ 无障碍设计

### 已实现

- ✅ 键盘导航支持
- ✅ 焦点状态可见
- ✅ 颜色对比度符合标准
- ✅ `prefers-reduced-motion` 支持
- ✅ 语义化 HTML 结构

### 待优化

- ⚠️ ARIA 属性补充
- ⚠️ 屏幕阅读器测试
- ⚠️ 高对比度模式支持

---

## 🎯 设计原则

### 1. 温暖而非冰冷

使用暖色调（琥珀、奶油白）替代传统医疗蓝绿，让用户感到被关怀。

### 2. 有机而非生硬

使用柔和的圆角、渐变和阴影，避免尖锐的几何形状。

### 3. 呼吸而非静止

通过微妙的动画（呼吸、脉冲）让界面有生命力。

### 4. 一致而非混乱

统一的字体、间距、颜色系统，确保视觉一致性。

### 5. 专注而非分散

清晰的视觉层次，引导用户关注重要内容。

---

## 🔧 使用示例

### 创建一个呼吸卡片

```vue
<template>
  <div class="breathing-card">
    <h3>卡片标题</h3>
    <p>卡片内容</p>
  </div>
</template>

<style scoped>
.breathing-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-normal);
}

.breathing-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
</style>
```

### 使用品牌渐变

```vue
<template>
  <button class="primary-btn">操作按钮</button>
</template>

<style scoped>
.primary-btn {
  background: var(--gradient-accent);
  border: none;
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-5);
  font-weight: var(--weight-semibold);
  color: var(--color-primary-dark);
  transition: all var(--transition-normal);
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
</style>
```

---

## 📊 设计验收清单

### 视觉质量

- [x] 使用 Fraunces 字体作为标题
- [x] 使用 Source Sans 3 作为正文
- [x] 应用暖色调色板
- [x] 使用有机圆角
- [x] 实现呼吸卡片效果

### 交互体验

- [x] 悬停状态提供视觉反馈
- [x] 过渡动画流畅自然
- [x] 焦点状态清晰可见
- [x] 响应式布局适配

### 品牌一致性

- [x] 统一的视觉语言
- [x] 一致的间距系统
- [x] 协调的颜色搭配
- [x] 专业的排版层次

---

## 🎨 设计亮点

### 1. 呼吸卡片

独特的签名设计元素，通过渐变边框和脉冲动画让界面有生命力。

### 2. 温暖配色

打破传统医疗应用的蓝绿色调，使用琥珀色和奶油白营造温暖感。

### 3. 有机设计

柔和的圆角、渐变和阴影，创造友好的视觉体验。

### 4. 品牌字体

使用 Fraunces 衬线字体作为标题，增添优雅和专业感。

### 5. 动态反馈

微妙的动画和过渡，让交互更加生动和直观。

---

**设计完成日期**: 2026-08-01
**设计方向**: 温润的清晰度
**设计原则**: 温暖、可信赖、有机、流动
