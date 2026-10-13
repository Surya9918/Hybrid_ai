namespace AuraCompanion.Design
{
    /// <summary>
    /// Hitodama-matched pixel-accurate visual design tokens.
    /// Strictly maintains theme parity, animation budgets, and per-monitor DPI scaling factors.
    /// </summary>
    public static class Tokens
    {
        // Palette Tokens
        public const string ColorBackgroundBase = "#0B0C10";      // Deep obsidian void
        public const string ColorBackgroundCard = "#14171E";      // Surface elevation 1
        public const string ColorBackgroundElevated = "#1F2833";  // Surface elevation 2
        public const string ColorAccentCyan = "#45F3FF";          // Electric Hitodama cyan
        public const string ColorAccentGlow = "#66FCF1";          // Orb energy peak
        public const string ColorTextPrimary = "#FFFFFF";         // 100% Contrast Text
        public const string ColorTextSecondary = "#C5C6C7";       // Muted slate text
        public const string ColorError = "#FF4E64";               // Error state amber-red
        public const string ColorWarning = "#FFB84E";             // Warning amber
        public const string ColorSuccess = "#4EFF9B";             // Success emerald

        // Glow & Shadow Tokens
        public const double OrbGlowRadius = 18.0;                 // Gaussian blur radius in DIPs
        public const double OrbGlowOpacity = 0.45;                // Energy opacity
        public const double WindowElevationShadowBlur = 24.0;
        public const double WindowElevationShadowOpacity = 0.35;

        // Geometry & Radii
        public const double CornerRadiusOrb = 32.0;               // Circular particle base (64x64)
        public const double CornerRadiusHUD = 16.0;               // Compact HUD
        public const double CornerRadiusIsland = 20.0;            // Expanded dynamic island
        public const double CornerRadiusDialog = 12.0;            // Modal & confirmation box
        public const double CornerRadiusButton = 8.0;             // Standard interactable

        // Spacing & Padding (4px grid)
        public const double SpacingXXS = 4.0;
        public const double SpacingXS = 8.0;
        public const double SpacingS = 12.0;
        public const double SpacingM = 16.0;
        public const double SpacingL = 24.0;
        public const double SpacingXL = 32.0;

        // Animation & Frame Pacing Targets
        public const double AnimationTargetFrameTimeMs = 16.666;   // 60 Hz budget (ms)
        public const double HighRefreshFrameTimeMs = 8.333;        // 120 Hz Surface Studio/Pro rate
        public const int DurationFastMs = 150;                    // Button tap / hover
        public const int DurationMediumMs = 280;                  // HUD expand / collapse
        public const int DurationOrbPulseMs = 1800;               // Idle breathing cycle
        public const int DurationTransitionMs = 400;              // State morphing

        // Easing: Cubic-Bezier(0.16, 1, 0.3, 1) - snappy deceleration curve
        public static readonly Windows.UI.Color CyanColor = Windows.UI.Color.FromArgb(255, 69, 243, 255);
        public static readonly Windows.UI.Color BaseVoidColor = Windows.UI.Color.FromArgb(255, 11, 12, 16);
    }
}
