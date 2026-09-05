import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { InfiniteCanvas } from "./InfiniteCanvas";
import "./spatial-board.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <InfiniteCanvas />
  </StrictMode>,
);
