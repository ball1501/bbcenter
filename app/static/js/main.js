
(function ($) {
    "use strict";

    
    /*==================================================================
    [ Validate ]*/
    var input = $('.validate-input .input100');

    $('.validate-form').on('submit',function(){
        var check = true;

        for(var i=0; i<input.length; i++) {
            if(validate(input[i]) == false){
                showValidate(input[i]);
                check=false;
            }
        }

        return check;
    });


    $('.validate-form .input100').each(function(){
        $(this).focus(function(){
           hideValidate(this);
        });
    });

    function validate(input) {
        // ตรวจสอบว่าเป็นช่องกรอก username หรือไม่
        if ($(input).attr('name') == 'username') {
            // Regex สำหรับ Username: อนุญาตเฉพาะตัวอักษรภาษาอังกฤษ ตัวเลข และ Underscore (_) ความยาว 3-20 ตัวอักษร
            if ($(input).val().trim().match(/^[a-zA-Z]{3,20}$/) == null) {
                return false;
            }
        }
        else {
            // สำหรับช่องอื่นๆ ตรวจสอบแค่ว่าไม่ได้ปล่อยว่างไว้
            if ($(input).val().trim() == '') {
                return false;
            }
        }
    }

    function showValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).addClass('alert-validate');
    }

    function hideValidate(input) {
        var thisAlert = $(input).parent();

        $(thisAlert).removeClass('alert-validate');
    }
    
    

})(jQuery);