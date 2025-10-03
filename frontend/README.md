# Chat App - Frontend

Frontend de aplicación de chat en tiempo real construido con Next.js 15, React 19 y shadcn/ui.

## 🚀 Stack Tecnológico

- **Framework:** Next.js 15.2.4 (App Router)
- **React:** 19
- **TypeScript:** 5
- **Estilos:** Tailwind CSS 4
- **UI Components:** shadcn/ui (Radix UI primitives)
- **Formularios:** React Hook Form + Zod
- **Temas:** next-themes
- **Iconos:** Lucide React
- **Notificaciones:** Sonner
- **Package Manager:** pnpm

## 📋 Características

- ✅ Interfaz de usuario moderna y responsive
- ✅ Sistema de temas (dark/light mode)
- ✅ Componentes UI reutilizables con shadcn/ui
- ✅ Validación de formularios con Zod
- 🚧 Chat en tiempo real con WebSockets (en desarrollo)
- 🚧 Autenticación de usuarios (en desarrollo)
- 🚧 Salas de chat 1-a-1 y grupales (en desarrollo)

## 🛠️ Instalación

### Prerrequisitos

- Node.js 18+
- pnpm (recomendado) o npm

### Instalación de dependencias

```bash
# Con pnpm (recomendado)
pnpm install

# O con npm
npm install
```

## 🏃 Scripts Disponibles

```bash
# Desarrollo - http://localhost:3000
pnpm dev

# Build de producción
pnpm build

# Iniciar en producción
pnpm start

# Linter
pnpm lint
```

## 🔌 Conexión con Backend

El frontend se conecta con la API FastAPI del backend:

- **REST API:** `http://localhost:8000`
- **WebSocket:** `ws://localhost:8000/ws`
- **Swagger Docs:** `http://localhost:8000/docs`

Asegúrate de que el backend esté corriendo antes de usar el frontend.

## 📁 Estructura del Proyecto

```
frontend/
├── app/              # App Router de Next.js (páginas y layouts)
├── components/       # Componentes React reutilizables
│   ├── ui/          # Componentes base de shadcn/ui
│   └── ...          # Componentes personalizados
├── hooks/           # Custom React hooks
├── lib/             # Utilidades y configuraciones
├── public/          # Assets estáticos
├── styles/          # Estilos globales
└── components.json  # Configuración de shadcn/ui
```

## 🎨 shadcn/ui

Este proyecto usa [shadcn/ui](https://ui.shadcn.com/) para componentes UI. Para agregar nuevos componentes:

```bash
npx shadcn@latest add [component-name]
```

## 🔧 Configuración

La configuración de Tailwind y componentes está en:

- `tailwind.config.js` - Configuración de Tailwind CSS
- `components.json` - Configuración de shadcn/ui
- `next.config.mjs` - Configuración de Next.js

## 📝 Notas de Desarrollo

- El proyecto usa el **App Router** de Next.js 15
- Los componentes están construidos con **Radix UI primitives** vía shadcn/ui
- Se usa **TypeScript** para type safety
- El sistema de temas está implementado con **next-themes**

## 🔗 Enlaces Relacionados

- [Documentación de Next.js](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Backend API Docs](http://localhost:8000/docs)
