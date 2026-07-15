const form = document.querySelector("#transaction-form");
const tableBody = document.querySelector("#transactions-body");
const message = document.querySelector("#message");
const formTitle = document.querySelector("#form-title");
const cancelEditButton = document.querySelector("#cancel-edit");
const searchInput = document.querySelector("#search");
const sortByInput = document.querySelector("#sort-by");
const sortOrderInput = document.querySelector("#sort-order");

const limit = 25;
let offset = 0;
let total = 0;

const fields = {
    transactionId: document.querySelector("#transaction-id"),
    accountNumber: document.querySelector("#account-number"),
    statementPeriod: document.querySelector("#statement-period"),
    transactionDate: document.querySelector("#transaction-date"),
    bookingDate: document.querySelector("#booking-date"),
    referenceNumber: document.querySelector("#reference-number"),
    transactionType: document.querySelector("#transaction-type"),
    amount: document.querySelector("#amount"),
    currency: document.querySelector("#currency"),
    counterpartyName: document.querySelector("#counterparty-name"),
    category: document.querySelector("#category"),
};

function addCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value ?? "";
    row.appendChild(cell);
}

function showMessage(text, isError = false) {
    message.textContent = text;
    message.className = isError ? "error" : "success";
}

function resetForm() {
    form.reset();
    fields.transactionId.value = "";
    formTitle.textContent = "Add transaction";
    cancelEditButton.hidden = true;
    message.textContent = "";
}

function getFormData() {
    return {
        account_number: fields.accountNumber.value,
        statement_period: fields.statementPeriod.value,
        transaction_date: fields.transactionDate.value,
        booking_date: fields.bookingDate.value,
        reference_number: fields.referenceNumber.value,
        transaction_type: fields.transactionType.value,
        amount: Number(fields.amount.value),
        currency: fields.currency.value,
        counterparty_name: fields.counterpartyName.value,
        category: fields.category.value,
    };
}

async function loadTransactions() {
    const parameters = new URLSearchParams();

    parameters.set("limit", limit.toString());
    parameters.set("offset", offset.toString());
    parameters.set("sort_by", sortByInput.value);
    parameters.set("sort_order", sortOrderInput.value);

    const search = searchInput.value.trim();

    if (search) {
        parameters.set("search", search);
    }

    console.log(
        `/api/transactions?${parameters.toString()}`
    );

    const response = await fetch(
        `/api/transactions?${parameters.toString()}`
    );

    const data = await response.json();

    total = data.total;
    tableBody.replaceChildren();

    for (const transaction of data.items) {
        const row = document.createElement("tr");

        addCell(row, transaction.id);
        addCell(row, transaction.account_number);
        addCell(row, transaction.transaction_date);
        addCell(row, transaction.reference_number);
        addCell(row, transaction.transaction_type);
        addCell(row, transaction.amount);
        addCell(row, transaction.currency);
        addCell(row, transaction.counterparty_name);
        addCell(row, transaction.category);

        const actionCell = document.createElement("td");
        const editButton = document.createElement("button");

        editButton.textContent = "Edit";
        editButton.addEventListener("click", () => {
            editTransaction(transaction.id);
        });

        actionCell.appendChild(editButton);
        row.appendChild(actionCell);
        tableBody.appendChild(row);
    }

    const currentPage = Math.floor(offset / limit) + 1;
    const totalPages = Math.max(Math.ceil(total / limit), 1);

    document.querySelector("#page-info").textContent =
        `Page ${currentPage} of ${totalPages} — ${total} records`;

    document.querySelector("#previous-page").disabled =
        offset === 0;

    document.querySelector("#next-page").disabled =
        offset + limit >= total;
}

async function editTransaction(transactionId) {
    const response = await fetch(
        `/api/transactions/${transactionId}`
    );

    if (!response.ok) {
        showMessage("Transaction could not be loaded.", true);
        return;
    }

    const transaction = await response.json();

    fields.transactionId.value = transaction.id;
    fields.accountNumber.value = transaction.account_number;
    fields.statementPeriod.value = transaction.statement_period;
    fields.transactionDate.value = transaction.transaction_date;
    fields.bookingDate.value = transaction.booking_date;
    fields.referenceNumber.value = transaction.reference_number;
    fields.transactionType.value = transaction.transaction_type;
    fields.amount.value = transaction.amount;
    fields.currency.value = transaction.currency;
    fields.counterpartyName.value = transaction.counterparty_name;
    fields.category.value = transaction.category;

    formTitle.textContent = `Edit transaction #${transaction.id}`;
    cancelEditButton.hidden = false;

    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const transactionId = fields.transactionId.value;
    const isEditing = transactionId !== "";

    const response = await fetch(
        isEditing
            ? `/api/transactions/${transactionId}`
            : "/api/transactions",
        {
            method: isEditing ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(getFormData()),
        }
    );

    const responseData = await response.json();

    if (!response.ok) {
        const errorMessage =
            responseData.detail instanceof Array
                ? responseData.detail
                    .map((error) => error.msg)
                    .join(", ")
                : responseData.detail;

        showMessage(
            errorMessage || "Request failed.",
            true
        );

        return;
    }

    resetForm();
    showMessage(
        isEditing
            ? "Transaction updated successfully."
            : "Transaction added successfully."
    );

    await loadTransactions();
});



document
    .querySelector("#search-button")
    .addEventListener("click", async () => {
        offset = 0;
        await loadTransactions();
    });

document
    .querySelector("#previous-page")
    .addEventListener("click", async () => {
        offset = Math.max(0, offset - limit);
        await loadTransactions();
    });

document
    .querySelector("#next-page")
    .addEventListener("click", async () => {
        if (offset + limit < total) {
            offset += limit;
            await loadTransactions();
        }
    });

cancelEditButton.addEventListener("click", resetForm);

sortByInput.addEventListener("change", async () => {
    offset = 0;
    await loadTransactions();
});

sortOrderInput.addEventListener("change", async () => {
    offset = 0;
    await loadTransactions();
});

loadTransactions();