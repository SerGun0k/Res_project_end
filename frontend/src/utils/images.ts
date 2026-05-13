/**
 * Генерация URL картинки товара.
 * Использует реальные изображения с placeholder для отсутствующих.
 */
export function getProductImage(
  category: string,
  brand: string,
  model: string,
  size: number = 300,
  imageUrl?: string | null,
): string {
  if (imageUrl) return imageUrl;

  // Реальные изображения с открытых источников
  // Для GPU - NVIDIA/AMD/Intel используют свои CDN
  if (category === 'GPU') {
    if (brand === 'NVIDIA') {
      return `https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/NVIDIA_logo_and_wordmark.svg/${size}px-NVIDIA_logo_and_wordmark.svg.png`;
    }
    if (brand === 'AMD') {
      return `https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/AMD_logo.svg/${size}px-AMD_logo.svg.png`;
    }
    if (brand === 'Intel') {
      return `https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Intel_logo_2023.svg/${size}px-Intel_logo_2023.svg.png`;
    }
  }

  // Для CPU
  if (category === 'CPU') {
    if (brand === 'AMD') {
      return `https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/AMD_logo.svg/${size}px-AMD_logo.svg.png`;
    }
    if (brand === 'Intel') {
      return `https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Intel_logo_2023.svg/${size}px-Intel_logo_2023.svg.png`;
    }
  }

  // Для остальных - генерируем SVG placeholder
  return generatePlaceholder(brand, model, size);
}

function generatePlaceholder(brand: string, model: string, size: number): string {
  // Генерируем уникальный цвет на основе названия
  let hash = 0;
  const str = brand + model;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  const bgColor = `hsl(${hue}, 40%, 85%)`;
  const textColor = `hsl(${hue}, 50%, 30%)`;

  const initial = brand.charAt(0).toUpperCase();

  return `data:image/svg+xml,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <rect width="${size}" height="${size}" fill="${bgColor}"/>
      <circle cx="${size/2}" cy="${size/2}" r="${size*0.35}" fill="${textColor}" opacity="0.15"/>
      <text x="${size/2}" y="${size/2}" text-anchor="middle" dy="0.35em" font-family="system-ui" font-size="${size*0.3}" font-weight="bold" fill="${textColor}">${initial}</text>
    </svg>
  `)}`;
}
