# 📱 Mobile Responsiveness Test Guide

This guide helps verify that the application works correctly across various mobile devices.

## 🛠️ Key Changes Implemented
1.  **Viewport Meta Tag**: Added `maximum-scale=1.0, user-scalable=no` to prevent auto-zoom on iOS inputs.
2.  **Responsive Layout**:
    *   Sidebar is now hidden on mobile and toggled via a hamburger menu.
    *   Added an overlay when the mobile menu is open.
    *   Main content area adjusts width automatically.
3.  **Form Optimization**:
    *   Input fields use `text-base` (16px) on mobile to prevent browser zooming.
    *   Padding and margins are reduced on smaller screens (`sm:` breakpoints).
    *   Buttons have larger touch targets.

## 🧪 How to Test

### 1. Using Chrome DevTools (Simulator)
1.  Open the app in Chrome.
2.  Press `F12` to open DevTools.
3.  Click the **Device Toolbar** icon (or press `Ctrl+Shift+M`).
4.  Select different devices from the dropdown:
    *   **iPhone SE** (Smallest screen)
    *   **iPhone 12 Pro** (Standard mobile)
    *   **Samsung Galaxy S8+** (Android aspect ratio)
    *   **iPad Air** (Tablet view)

### 2. Verification Checklist

#### 🔐 Login Page
- [ ] **Card Width**: Should fit within the screen with small margins on the side.
- [ ] **Inputs**: Tapping an input should NOT zoom the page.
- [ ] **Text Size**: Labels and input text should be readable (16px).
- [ ] **Button**: "Sign In" button should be easy to tap (full width).
- [ ] **Background**: Gradient should cover the full height (`min-h-screen`).

#### 📝 Signup Page
- [ ] **Grid Layout**:
    *   On **Mobile**: Fields should stack vertically (1 column).
    *   On **Tablet/Desktop**: Fields should be side-by-side (2 columns).
- [ ] **Scrolling**: Page should scroll smoothly without horizontal scrolling.

#### 🧭 Dashboard Layout (After Login)
- [ ] **Header**:
    *   Should show a **Hamburger Menu** icon on the left.
    *   Should show the Page Title (e.g., "Dashboard").
    *   Should show the **Logout** icon (text might be hidden on very small screens).
- [ ] **Sidebar**:
    *   Should be **HIDDEN** by default.
    *   Clicking the **Hamburger Menu** should slide the sidebar in.
    *   Clicking the **Overlay** (dark background) should close the sidebar.
    *   Clicking a **Link** should navigate and close the sidebar.
- [ ] **Content**:
    *   Tables and cards should not overflow horizontally (or should have internal scroll).

### 3. Real Device Testing (Optional)
If you have deployed to Vercel:
1.  Open the URL on your actual phone.
2.  Try to log in.
3.  Verify that the keyboard doesn't break the layout.

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
| :--- | :--- | :--- |
| **Page Zooms on Input** | Font size < 16px on iOS | Ensure `text-base` class is used on inputs for mobile. |
| **Horizontal Scroll** | Fixed width elements | Use `w-full`, `max-w-full`, or `overflow-x-hidden`. |
| **Sidebar Won't Close** | Z-index issue | Check `z-30` on sidebar and `z-20` on overlay. |
| **Header Text Cut Off** | Long username/title | Use `truncate` class on text elements. |
