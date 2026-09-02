const BOOK_SLUGS = ["caderno1", "caderno28", "caderno43", "peniche", "inventario"];

const bookList = document.getElementById("book-list");

BOOK_SLUGS.forEach((slug) => {
  fetch(`books/${slug}/manifest.json`)
    .then((response) => response.json())
    .then((manifest) => {
      const card = document.createElement("a");
      card.className = "book-card";
      card.href = `viewer.html?book=${slug}`;

      const cover = document.createElement("img");
      cover.className = "book-cover";
      cover.src = `books/${slug}/${manifest.pages[0].image}`;
      cover.alt = "";

      const title = document.createElement("h2");
      title.textContent = manifest.title;

      const pageCount = document.createElement("p");
      pageCount.textContent = `${manifest.page_count} páginas`;

      card.append(cover, title, pageCount);
      bookList.appendChild(card);
    });
});
