import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const isProduction = mode === 'production';
  return {
    base: isProduction ? '/app/' : '/',
    plugins: [react(), tailwindcss()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/llm': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/extract_feature': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/select_algorithm': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/solve_equation': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/evaluate_result': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/health': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
        },
        '/ws': {
          target: env.VITE_API_BASE_URL || 'http://127.0.0.1:8001',
          changeOrigin: true,
          ws: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'lucide-vendor': ['lucide-react'],
          },
        },
      },
    },
  };
});
