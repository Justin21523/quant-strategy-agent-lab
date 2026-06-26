export function createPlaceholderPage({ title, description, phase }) {
  const element = document.createElement("section");
  element.className = "page placeholder-page";
  element.innerHTML = `
    <div class="placeholder-panel">
      <p class="eyebrow">${phase}</p>
      <h1>${title}</h1>
      <p>${description}</p>
      <div class="placeholder-panel__note">
        <strong>Why this page exists now</strong>
        <p>
          Phase 0 establishes routing and ownership boundaries. The real domain behavior will be added
          in its assigned phase with tests and documented API contracts.
        </p>
      </div>
      <a class="button button--secondary" href="#/">Return to overview</a>
    </div>`;
  return element;
}
