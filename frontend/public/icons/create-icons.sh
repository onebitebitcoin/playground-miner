#!/bin/bash

# Create simple SVG icon and convert to different sizes
# This creates a simple Bitcoin symbol icon

create_svg() {
cat > icon.svg << 'SVGEOF'
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" rx="64" fill="#111827"/>
  <g transform="translate(128, 128)">
    <circle cx="128" cy="128" r="120" fill="none" stroke="#ffffff" stroke-width="16"/>
    <path d="M80 80 L80 176 M176 80 L176 176 M80 128 L176 128" stroke="#ffffff" stroke-width="12" fill="none" stroke-linecap="round"/>
    <path d="M104 64 L104 192 M152 64 L152 192" stroke="#ffffff" stroke-width="8" fill="none" stroke-linecap="round"/>
  </g>
</svg>
SVGEOF
}

# Create base SVG
create_svg

# Create PNG files (using rsvg-convert if available, or creating placeholder files)
for size in 72 96 128 144 152 192 384 512; do
  # Create a simple placeholder file (in real implementation, you'd use proper image conversion)
  cp icon.svg icon-${size}x${size}.png
done

echo "Icons created (placeholders - replace with proper PNG conversion)"
