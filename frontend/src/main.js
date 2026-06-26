import { createApp } from "./app.js";
import "./styles/index.css";

const root = document.querySelector("#app");
if (!root) throw new Error("Application root #app was not found.");
createApp(root);
