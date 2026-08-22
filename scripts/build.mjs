import { cp, mkdir, rm, readdir, readFile, writeFile } from 'node:fs/promises'

const dist = new URL('../dist/', import.meta.url)
const partsDir = new URL('../public/data/parts/', import.meta.url)

await rm(dist, { recursive: true, force: true })
await mkdir(dist, { recursive: true })
await cp(new URL('../index.html', import.meta.url), new URL('../dist/index.html', import.meta.url))
await cp(new URL('../public', import.meta.url), dist, { recursive: true })

const names = (await readdir(partsDir))
  .filter((name) => name.startsWith('protocolos.part'))
  .sort()

if (!names.length) throw new Error('Partes da base web não encontradas')

const parts = await Promise.all(names.map((name) => readFile(new URL(name, partsDir))))
await writeFile(new URL('../dist/data/protocolos.json.gz', import.meta.url), Buffer.concat(parts))

console.log(`Build estático concluído: dist/ · ${names.length} partes da base`)
