import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import * as simpleIcons from 'simple-icons'
import { icons as featherIcons } from 'feather-icons'
import academiconsData from '@iconify-json/academicons/icons.json' assert { type: 'json' }

// Node.js v18対応のディレクトリパス取得
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const icons = {};

for (const key in featherIcons) {
  const icon = featherIcons[key]
  icons[icon.name] = `<svg class="icon icon-${icon.name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><title>${icon.name}</title>${icon.contents}</svg>`
}

for (const key in simpleIcons) {
  const icon = simpleIcons[key]
  icons['brand-' + icon.slug] = `<svg class="icon icon-brand-${icon.slug}" viewBox="0 0 24 24" fill="currentColor"><title>${icon.title}</title><path d="${icon.path}"/></svg>`
}

// Academicons の処理（より安全な版）
if (academiconsData && academiconsData.icons) {
  for (const key in academiconsData.icons) {
    const icon = academiconsData.icons[key]
    
    let iconBody = icon.body || ''
    
    // HTMLタグを含む場合はクリーンアップ
    if (iconBody.includes('<path')) {
      // <path>タグを抽出してd属性の値だけを取得
      const pathMatch = iconBody.match(/d="([^"]+)"/);
      if (pathMatch) {
        iconBody = pathMatch[1];
      }
    }
    
    icons['ai-' + key] = `<svg class="icon icon-ai-${key}" viewBox="0 0 512 512" fill="currentColor"><title>${key}</title><path d="${iconBody}"/></svg>`
  }
}

fs.writeFileSync(
  path.join(__dirname, '../../data/m10c/icons.json'),
  JSON.stringify(icons, null, 2),
  'utf8',
)
