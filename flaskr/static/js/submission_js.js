window.onload = function(){
    // Image display event listeners
    armor_input = document.getElementById("armorTexture")
    armor_display = document.getElementById("armorTextureDisplay")
    armor_input.addEventListener('input', function(e){
        [file] = armor_input.files
        if(file){
            armor_display.src = URL.createObjectURL(file)
        }
    })

    item_input = document.getElementById("itemTexture")
    item_display = document.getElementById("itemTextureDisplay")
    item_input.addEventListener('input', function(e){
        [file] = item_input.files
        if(file){
            item_display.src = URL.createObjectURL(file)
        }
    })

    // Submission event listener
    form = document.getElementById("SubmissionForm")
    button = document.getElementById("submit")
    button.addEventListener("click", function(e){
        form.submit();
    });
};