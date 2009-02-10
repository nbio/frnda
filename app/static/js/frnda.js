(function(){
    var placeholder = function(evt) {
        var e = evt.target;
        var p = e.getAttribute("placeholder");
        if(!p)
            return;
        $(e).removeClass("placeholder");
        if(evt.type == "focus" && e.value == p || e.value == "") {
            e.value = "";
        } else if(e.value.match(/^\s+$|^$/)) {
            e.value = p;
            $(e).addClass("placeholder");
        }
    };
    
    
    var formSubmit = function(evt) {
        $(evt.target).find("input[placeholder]").triggerHandler("focus");
    };
    
    
    var mirror = function(evt) {
        var e = evt.target;
        $(".mirror-" + e.id).text(e.value);
    };
    
    
    var hvOn = function(evt) {
        $(".tip").hide();
        $(this).addClass("hv-hover");
        var id = "#tip-" + this.className.match(/\Whv-(\S+)/)[1];
        if(!id)
            return;
        $(id).show();
    };
    
    
    var hvOut = function(evt) {
        $(this).removeClass("hv-hover");
        $(".tip").hide();
    };
    
    
    /* setup */
    $(document).ready(function() {
        $("input[placeholder]").focus(placeholder);
        $("input[placeholder]").blur(placeholder);
        $("input[placeholder]").triggerHandler("blur");
        
        $("form").submit(formSubmit);
        
        $(".mirror").change(mirror).keyup(mirror).blur(mirror);
        $(".hv").hover(hvOn, hvOut);
    })
})();
