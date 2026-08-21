import { cp, mkdir, rm } from 'node:fs/promises'

const dist = new URL('../dist/', import.meta.url)
const root = new URL('../', import.meta.url)

await rm(dist, { recursive: true, force: true })
await mkdir(dist, { recursive: true })
await cp(new URL('../index.html', import.meta.url), new URL('../dist/index.html', import.meta.url))
await cp(new URL('../public', import.meta.url), dist, { recursive: true })

console.log('Build estático concluído: dist/')
