export function createPhaseCard({ number, title, description, status }) {
  const article = document.createElement("article");
  article.className = "phase-card";
  article.innerHTML = `
    <div class="phase-card__header">
      <span>Phase ${number}</span>
      <span class="phase-card__status" data-status="${status}">${status}</span>
    </div>
    <h3>${title}</h3>
    <p>${description}</p>`;
  return article;
}
