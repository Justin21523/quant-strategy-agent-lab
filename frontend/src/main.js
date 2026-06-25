import './styles/index.css';
import { createApp } from './app.js';

const root = document.querySelector('#app');

if (!(root instanceof HTMLElement)) {
  throw new Error('Application root #app was not found.');
}

const app = createApp({ root });
app.start();
