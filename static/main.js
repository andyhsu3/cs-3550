import { $ } from "/static/jquery/src/jquery.js";

function say_hi(elt) {
    console.log("Welcome to", elt.text());
}

say_hi($("h1"));

// this is where we make sure that it targets all tables that have the class="sortable". focus sortable only.
$(document).ready(function () {
    $(".sortable").each(function () {
        make_table_sortable($(this));
    });
});

// function created in phase 2 to sort tables based on grades.
function make_table_sortable($table) {
     // select all headers in the table that have the class "sort-column" with the JQuery "on"
    const $headers = $table.find("th.sort-column");

    // Phase 3 HW 6 - add role button for accessibility
    $headers.attr("role", "button");

    $headers.on("click", function () {
        const $this = $(this);
        const columnIndex = $this.index();
        const rows = $table.find("tbody tr").toArray();

         // three states: unsorted, sort-asc, or sort-desc. (set sort-asc on its own and the other two together).
        const isAscending = $this.hasClass("sort-asc");
        const isDescending = $this.hasClass("sort-desc");

        // Clear sort classes on all headers
        $headers.removeClass("sort-asc sort-desc").attr("aria-sort", "none");

        // here we want to check that if the cell is clicked -- we will determine the state of the table.
        // if it is ascending -- make it descending, otherwise (it's desc or unsort) make it ascending.
        // Phase 3 changing this -- adds else if (isDescending) --> moves to original sort and else is unsorted which changes to ascending order.
        // Phase 3 also changes the code with a new helper for the index.html as well (sort by due dates)
        if (isAscending) {
            $this.addClass("sort-desc").attr("aria-sort", "descending");
            rows.sort((a, b) => {
                const valA = getCellValue($(a).find("td").eq(columnIndex));
                const valB = getCellValue($(b).find("td").eq(columnIndex));
                return valB - valA;
            });
        } else if (isDescending) {
            rows.sort((a, b) => {
                const indexA = $(a).data("index");
                const indexB = $(b).data("index");
                return indexA - indexB;
            });
        } else {
            $this.addClass("sort-asc").attr("aria-sort", "ascending");
            rows.sort((a, b) => {
                const valA = getCellValue($(a).find("td").eq(columnIndex));
                const valB = getCellValue($(b).find("td").eq(columnIndex));
                return valA - valB;
            });
        }
        $(rows).appendTo($table.find("tbody"));
    });

    // this is a helper method where if there is data-value then we want to use the data that is given to us.
    // otherwise we will just use the normal text that was given to us.
    function getCellValue($cell) {
        return parseFloat($cell.data("value")) || parseFloat($cell.text().replace("%", "")) || 0;
    }
}

function make_grade_hypothesized($table)
{
    // step 1 is to create the button and add it right before the table.
    const $hypothesisButton = $('<button>')
        .text("Hypothesize")
        .attr("id", "hypothesize-button");

    $table.before($hypothesisButton);
    
    // click event listener - clicking a button adds a "hypothesized" class and changes button to actual gradses.
    // if hypothesized class is present, remove and change button back to Hypothesize.
    $hypothesisButton.on("click", function () {
        // we reset everything here -- including all %'s back to Not Due or Ungraded.
        if($table.hasClass("hypothesized"))
        {
            $table.removeClass("hypothesized");
            $hypothesisButton.text("Hypothesize");

            $table.find("tbody td").each(function () {
                const $tableCell = $(this);
                if($tableCell.find("input").length > 0)
                {
                    const originalCellText = $tableCell.data("original-text");
                    if (originalCellText !== undefined)
                    {
                        $tableCell.empty().text(originalCellText);
                    }
                }
            });
            computeTotalGrade($table);
        }
        else
        {
            $table.addClass("hypothesized");
            $hypothesisButton.text("Actual Grades");

            // here, we can allow input to be given for not due or ungraded cells.
            $table.find("tbody td").each(function() {
                const $tableCell = $(this);
                const textInCell = $tableCell.text().trim();

                if(textInCell == "Not Due" || textInCell == "Ungraded")
                {
                    $tableCell.data("original-text", textInCell);
                    const $hypothesizedInput = $('<input>')
                        .attr("type", "number")
                        .attr("min", 0)
                        .attr("max", 100)
                        .attr("placeholder", "Enter grade")
                        .on("keyup", function() {
                            computeTotalGrade($table);
                        });
                    $tableCell.empty().append($hypothesizedInput);
                }
            });
            computeTotalGrade($table);
        }
    });
}

// this connects the function above to the profile html class
$(document).ready(function (){
    if ($("body").hasClass("profile") && $(".sortable").length){
        make_grade_hypothesized($(".sortable"));
    }
});

// this function computes the current grade using data-weight in the html -- will be used in both versions 
// (hypothesized and actual grades) so will be called few times in the make_grade_hypothesized function.
function computeTotalGrade($table) {
    let overallWeight = 0;
    let earnedPoints = 0;

    $table.find("tbody tr").each(function () {
        const $tableRow = $(this);
        const $tableCell = $tableRow.find("td.scored-header");
        const weight = parseFloat($tableCell.data("weight")) || 0;

        // if we're in hypothesized mode, 
        if ($table.hasClass("hypothesized")) 
        {
            const $input = $tableCell.find("input");
            if ($input.length > 0) {
                const inputValue = $input.val();
                if (inputValue.trim() !== "") 
                {
                    overallWeight += weight;
                    earnedPoints += (parseFloat(inputValue) / 100) * weight;
                }
            } 
            // we should only look at grades that are "not due" or "ungraded".
            else 
            {
                const assignmentGrade = parseFloat($tableCell.data("value"));
                const cellText = $tableCell.text().trim();
                if (cellText === "Missing") {
                    overallWeight += weight;
                } else if (cellText !== "Not Due" && cellText !== "Ungraded") {
                    overallWeight += weight;
                    earnedPoints += (assignmentGrade / 100) * weight;
                }
            }
        } 
        // otherwise we're in the actual grade mode
        else 
        {
            const assignmentGrade = parseFloat($tableCell.data("value"));
            const cellText = $tableCell.text().trim();
            if (cellText === "Missing") {
                overallWeight += weight;
            } else if (cellText !== "Not Due" && cellText !== "Ungraded") {
                overallWeight += weight;
                earnedPoints += (assignmentGrade / 100) * weight;
            }
        }
    });
    const finalGrade = overallWeight > 0 ? (earnedPoints / overallWeight) * 100 : 100;
    $table.find("tfoot .scored-header").text(`${finalGrade.toFixed(2)}%`);
}

// phase 4
function make_form_async($form)
{
    // add in a submit handler -- call the preventDefault method to prevent form from being submitted normally
    $form.on("submit", function (event) {
        event.preventDefault();

        // sete the formData object, the URL here, and the mimetype before we submit the form in AJAX。
        const formData = new FormData(this);
        const actionURL = $form.attr("action");
        const mimeType = $form.attr("enctype");

        $.ajax({
            url: actionURL,
            method: "POST",
            data: formData,
            processData: false,
            contentType: false,
            mimeType: mimeType,

            // here we do the success and error messages -- alongside success, we disable resubmitting
            success: function (response) {
                $form.replaceWith('<p class="success-message">Assignment upload was successful</p>');
            },

            error: function(xhr){
                console.log("Error submitting the assignment: ", xhr.responseText);

                const $fileInput = $form.find('input[type="file"]');
                const $submitButton = $form.find('button[type="submit"]');

                $fileInput.prop("disabled", false);
                $submitButton.prop("disabled", false);
            }
        });
    });
}

// invoke on the submission form of the assignment
$(document).ready(function (){
    const $asyncForm = $("form.async-form");
    if ($asyncForm.length)
    {
        make_form_async($asyncForm);
    }
})