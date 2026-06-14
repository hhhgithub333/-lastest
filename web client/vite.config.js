import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
    plugins: [vue()],
    server: {
        port: 5173,
        host: true
    },
    build: {
        rollupOptions: {
            input: {
                main: path.resolve(__dirname, 'index.html'),
                floating: path.resolve(__dirname, 'src/renderer/floating.html')
            }
        }
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src/renderer')
        }
    }
});