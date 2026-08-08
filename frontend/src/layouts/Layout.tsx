import { Outlet } from "react-router-dom";

export function Layout() {
  return (
    <main>
      <header>
        <h1>
          NETI <span className="muted">— Non-Exploitable Test Integrity</span>
        </h1>
      </header>
      <Outlet />
    </main>
  );
}
