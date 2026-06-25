import { createElement } from '../core/dom.js';

export function createCapabilityCard({ label, status }) {
  const article = createElement('article', { className: 'capability-card' });
  const indicator = createElement('span', {
    className: 'capability-card__indicator',
    attributes: { 'data-status': status, 'aria-hidden': 'true' },
  });
  const body = createElement('div');
  const title = createElement('p', { text: label });
  const detail = createElement('small', {
    text: status === 'ready' ? 'Ready in Phase 0' : 'Planned, not faked',
  });

  body.append(title, detail);
  article.append(indicator, body);
  return article;
}
