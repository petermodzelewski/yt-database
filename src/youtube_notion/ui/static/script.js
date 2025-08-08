document.addEventListener('DOMContentLoaded', () => {
    let ws;
    const todoColumn = document.querySelector('#todo .cards');
    const inprogressColumn = document.querySelector('#inprogress .cards');
    const doneColumn = document.querySelector('#done .cards');
    const addBtn = document.querySelector('.add-btn');
    const inputContainer = document.querySelector('.input-container');
    const urlInput = document.querySelector('.input-container input');
    const addUrlBtn = document.querySelector('.input-container button');
    const logModal = document.getElementById('log-modal');
    const logContent = document.getElementById('log-content');
    const closeModalBtn = document.querySelector('.close-btn');

    const cardData = {};

    function connect() {
        ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const { status, url, message, progress, error, metadata } = data;

        if (status === 'queued') {
            addCard(todoColumn, url, {});
        } else if (status === 'processing') {
            moveCard(url, inprogressColumn);
            updateCardStatus(url, message, progress);
        } else if (status === 'done') {
            cardData[url] = metadata;
            moveCard(url, doneColumn);
            updateCardStatus(url, 'Done', 100);
            updateCardTitle(url, metadata.title);
            addLogButton(url);
        } else if (status === 'failed') {
            moveCard(url, doneColumn);
            updateCardStatus(url, `Failed: ${error}`, 0);
        }
    };

        ws.onclose = () => {
            console.log('WebSocket disconnected. Trying to reconnect...');
            setTimeout(connect, 1000);
        };
    }

    connect();

    addBtn.addEventListener('click', () => {
        inputContainer.style.display = 'flex';
    });

    addUrlBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (url) {
            ws.send(url);
            urlInput.value = '';
            inputContainer.style.display = 'none';
        }
    });

    closeModalBtn.addEventListener('click', () => {
        logModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === logModal) {
            logModal.style.display = 'none';
        }
    });

    function createCard(url, metadata) {
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.url = url;

        const videoId = getYouTubeVideoId(url);
        if (videoId) {
            const img = document.createElement('img');
            img.src = `https://img.youtube.com/vi/${videoId}/0.jpg`;
            card.appendChild(img);
        }

        const title = document.createElement('div');
        title.className = 'title';
        title.textContent = metadata.title || url;
        card.appendChild(title);

        const statusContainer = document.createElement('div');
        statusContainer.className = 'status-container';

        const status = document.createElement('div');
        status.className = 'status';
        statusContainer.appendChild(status);

        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        const progress = document.createElement('div');
        progress.className = 'progress';
        progressBar.appendChild(progress);
        statusContainer.appendChild(progressBar);

        card.appendChild(statusContainer);

        const actions = document.createElement('div');
        actions.className = 'actions';
        card.appendChild(actions);

        return card;
    }

    function addCard(column, url, metadata) {
        const card = createCard(url, metadata);
        card.classList.add('card-enter');
        column.appendChild(card);
        setTimeout(() => {
            card.classList.remove('card-enter');
        }, 300);
    }

    function updateCardTitle(url, newTitle) {
        const card = document.querySelector(`.card[data-url="${url}"]`);
        if (card) {
            const title = card.querySelector('.title');
            title.textContent = newTitle;
        }
    }

    function moveCard(url, toColumn) {
        const card = document.querySelector(`.card[data-url="${url}"]`);
        if (card) {
            toColumn.appendChild(card);
        }
    }

    function updateCardStatus(url, statusText, progressValue) {
        const card = document.querySelector(`.card[data-url="${url}"]`);
        if (card) {
            const status = card.querySelector('.status');
            status.textContent = statusText;

            const progress = card.querySelector('.progress');
            progress.style.width = `${progressValue}%`;
        }
    }

    function addLogButton(url) {
        const card = document.querySelector(`.card[data-url="${url}"]`);
        if (card) {
            const actions = card.querySelector('.actions');
            const logButton = document.createElement('button');
            logButton.textContent = 'View Log';
            logButton.addEventListener('click', async () => {
                const videoId = getYouTubeVideoId(url);
                if (videoId) {
                    try {
                        const response = await fetch(`/logs/${videoId}`);
                        if (response.ok) {
                            const logText = await response.text();
                            logContent.textContent = logText;
                        } else {
                            logContent.textContent = 'Could not load log file.';
                        }
                    } catch (error) {
                        logContent.textContent = `Error loading log: ${error}`;
                    }
                    logModal.style.display = 'block';
                }
            });
            actions.appendChild(logButton);
        }
    }

    function getYouTubeVideoId(url) {
        const regex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }
});
