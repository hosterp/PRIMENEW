openerp.hiworth_project_management.quickadd = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.hiworth_project_management = instance.web.hiworth_project_management || {};

    instance.web.views.add('tree_job_summary_quickadd', 'instance.web.hiworth_project_management.QuickAddListView');
    instance.web.hiworth_project_management.QuickAddListView = instance.web.ListView.extend({
        init: function() {
            this._super.apply(this, arguments);
           
        },
        start:function(){
            var tmp = this._super.apply(this, arguments);
            var self = this;
            var defs = [];
            this.$el.parent().prepend(QWeb.render("JobSummaryQuickAdd", {widget: this}));
            return tmp;
        },
        
    });
};
