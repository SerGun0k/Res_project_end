// Маппинг ключей спецификаций → человекочитаемые названия
const SPEC_LABELS: Record<string, string> = {
  // GPU
  memory_gb: 'Объём видеопамяти',
  memory_type: 'Тип видеопамяти',
  memory_bus: 'Шина памяти',
  tdp_watts: 'TDP (энергопотребление)',
  base_clock_mhz: 'Базовая частота чипа',
  boost_clock_mhz: 'Турбо частота чипа',
  cuda_cores: 'CUDA-ядра',
  ray_tracing: 'Трассировка лучей',
  dlss: 'DLSS (AI-апскейлинг)',
  interface: 'Интерфейс подключения',
  length_mm: 'Длина карты',
  connectors: 'Видеовыходы',
  recommended_psu: 'Рекомендуемый БП',

  // CPU
  cores: 'Количество ядер',
  threads: 'Количество потоков',
  base_clock_ghz: 'Базовая частота',
  boost_clock_ghz: 'Максимальная частота',
  socket: 'Сокет',
  l3_cache_mb: 'Кэш L3',
  lithography_nm: 'Техпроцесс',
  pcie_version: 'Версия PCIe',
  integrated_graphics: 'Встроенная графика',
  unlocked: 'Разблокированный множитель',

  // RAM
  type: 'Тип памяти',
  speed_mhz: 'Частота',
  cas_latency: 'Тайминги (CL)',
  voltage: 'Напряжение',
  modules: 'Количество модулей',
  heatsink: 'Радиатор охлаждения',
  ecc: 'ECC (коррекция ошибок)',

  // SSD / HDD / M2
  capacity_gb: 'Объём',
  read_mbps: 'Скорость чтения',
  write_mbps: 'Скорость записи',
  iops_read: 'IOPS чтение',
  iops_write: 'IOPS запись',
  nand_type: 'Тип NAND',
  tbw: 'Ресурс (TBW)',
  rpm: 'Скорость вращения',
  cache_mb: 'Объём кэша',
  form_factor: 'Форм-фактор',

  // PSU
  watts: 'Мощность',
  efficiency: 'Сертификат эффективности',
  modular: 'Модульность',
  pfc: 'Активный PFC',
  fan_size: 'Размер вентилятора',
  atx_version: 'Версия ATX',

  // COOLING
  cooler_type: 'Тип охлаждения',
  max_tdp_watts: 'Макс. TDP',
  noise_dba: 'Уровень шума',
  fan_rpm: 'Обороты вентилятора',
  height_mm: 'Высота',
  fan_count: 'Количество вентиляторов',

  // Общее
  brand: 'Бренд',
  model: 'Модель',
  country: 'Страна-производитель',
  warranty: 'Гарантия',
  weight_g: 'Вес',
};

// Форматирование значений
function formatSpecValue(key: string, value: unknown): string {
  if (value === null || value === undefined) return '—';

  // Булевы значения
  if (typeof value === 'boolean') {
    return value ? 'Да' : 'Нет';
  }

  // Числовые значения с единицами
  if (typeof value === 'number') {
    const unitMap: Record<string, string> = {
      memory_gb: 'ГБ',
      capacity_gb: 'ГБ',
      tdp_watts: 'Вт',
      max_tdp_watts: 'Вт',
      base_clock_ghz: 'ГГц',
      boost_clock_ghz: 'ГГц',
      base_clock_mhz: 'МГц',
      boost_clock_mhz: 'МГц',
      speed_mhz: 'МГц',
      l3_cache_mb: 'МБ',
      cache_mb: 'МБ',
      noise_dba: 'дБА',
      height_mm: 'мм',
      length_mm: 'мм',
      weight_g: 'г',
      fan_rpm: 'об/мин',
      rpm: 'об/мин',
      watts: 'Вт',
      tbw: 'ТБ',
      voltage: 'В',
      lithography_nm: 'нм',
      memory_bus: 'бит',
    };

    const unit = unitMap[key];
    return unit ? `${value} ${unit}` : String(value);
  }

  return String(value);
}

export default function SpecsTable({ specs }: { specs: Record<string, unknown> }) {
  const skipKeys = ['release_date', 'image_url'];

  // Сортируем: важные ключи первыми
  const priorityKeys = [
    'capacity_gb', 'memory_gb', 'memory_type', 'memory_bus',
    'cores', 'threads', 'base_clock_ghz', 'boost_clock_ghz',
    'socket', 'tdp_watts', 'read_mbps', 'write_mbps',
    'interface', 'watts', 'efficiency', 'type', 'speed_mhz',
    'country', 'brand', 'model',
  ];

  const entries = Object.entries(specs).filter(([key]) => !skipKeys.includes(key));

  entries.sort((a, b) => {
    const ai = priorityKeys.indexOf(a[0]);
    const bi = priorityKeys.indexOf(b[0]);
    if (ai === -1 && bi === -1) return 0;
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  return (
    <table className="w-full text-sm">
      <tbody>
        {entries.map(([key, value]) => {
          const label = SPEC_LABELS[key] || key.replace(/_/g, ' ');
          const formattedValue = formatSpecValue(key, value);

          return (
            <tr key={key} className="border-b border-slate-100 dark:border-slate-800">
              <td className="py-2 pr-4 font-medium text-slate-600 dark:text-slate-400">
                {label}
              </td>
              <td className="py-2 text-slate-900 dark:text-slate-100">
                {formattedValue}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
