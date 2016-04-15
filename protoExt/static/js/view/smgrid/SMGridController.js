/*jslint nomen: true, sloppy : true, white : true, sub : true */
/*global Ext */
/*global _SM */
/*global ProtoUL */

Ext.define('Softmachine.view.smgrid.SMGridController', {
    extend : 'Ext.Base',

    // Parametros de entrada
    myMeta : null,
    myGrid : null,
    store : null,

    constructor : function(config){
        Ext.apply(this, config || {});

    },

    addNavigationPanel : function(){
        /*
         * Configuracion del NavigationPanel, tiene en cuenta el manejo de detalles y agrega el
         * maximo del almacenamiento local.
         * 
         */

        var me = this, myGrid = this.myGrid, navPanel = [
            '-'
        ], myNavPanel, comboPageSize;

        comboPageSize = Ext.create('Ext.form.ComboBox', {
            name : 'perpage',
            width : 60,
            store : Ext.create('Ext.data.ArrayStore', {
                fields : [
                    'id'
                ],
                data : _SM._ComboPageSize
            }),
            mode : 'local',
            value : '50',
            listWidth : 60,
            triggerAction : 'all',
            displayField : 'id',
            valueField : 'id',
            editable : false,
            forceSelection : true
        });

        comboPageSize.on('select', function(combo, record){
            myGrid.store.pageSize = parseInt(combo.getValue(), 10);
            myGrid.store.load();
            if (myGrid.store.currentPage != 1) {
                myGrid.store.loadPage(1);
            }
        }, myGrid);

        // Extraccion de grilla detalle
        if (myGrid.protoIsDetailGrid) {
            navPanel.push({
                text : _SM.__language.GridNav_In_New_Tab,
                iconCls : 'icon-promote',
                scope : me,
                handler : onMenuPromoteDetail
            });
        }

        navPanel.push(comboPageSize, _SM.__language.GridNav_PageSize);

        myNavPanel = {
            xtype : 'pagingtoolbar',
            border : false,
            dock : 'bottom',
            store : myGrid.store,
            displayInfo : true,
            items : navPanel,
            afterPageText : _SM.__language.GridNav_Total + ' {0}',
            beforePageText : _SM.__language.GridNav_Page,

            firstText : _SM.__language.GridNav_First_Page,
            nextText : _SM.__language.GridNav_Next_Page,
            prevText : _SM.__language.GridNav_Previous_Page,
            lastText : _SM.__language.GridNav_Last_Page,
            refreshText : _SM.__language.GridNav_Refresh,

            displayMsg : _SM.__language.GridNav_Current + ' : {0} - {1} '
                    + _SM.__language.GridNav_Total + ' {2}'
        // emptyMsg: "No register to display"
        };

        myGrid.addDocked(myNavPanel);

        function onMenuPromoteDetail(){
            _SM.vp_TabContainer.controller.addTabPanel(myGrid.viewCode, myGrid.mdFilter, myGrid.detailTitle);
        }

    },

    addGridTools : function(editMode){

        var hideTool = !editMode, editTools;

        editTools = [
            {
                itemId : 'toolFormAdd',
                tooltip : _SM.__language.GridBtn_Ttip_Add_Form,
                type : 'formAdd',
                width : 20,
                hidden : hideTool,
                scope : this,
                handler : this.onEditAction
            },
            {
                itemId : 'toolFormUpd',
                tooltip : _SM.__language.GridBtn_Ttip_Edit_Form,
                hidden : hideTool,
                type : 'formUpd',
                width : 20,
                scope : this,
                handler : this.onEditAction
            },
            {
                itemId : 'toolRowDel',
                type : 'rowDel',
                tooltip : _SM.__language.GridBtn_Ttip_Del_Record,
                hidden : hideTool,
                width : 30,
                scope : this,
                handler : this.onEditAction
            },
            {
                itemId : 'toolFormView',
                tooltip : _SM.__language.GridBtn_Ttip_Read_Only,
                type : 'formView',
                width : 20,
                scope : this,
                handler : this.onEditAction
            },
            {
                itemId : 'toolRowCopy',
                tooltip : _SM.__language.GridBtn_Ttip_Copy_Row,
                type : 'rowCopy',
                hidden : hideTool,
                width : 20,
                scope : this,
                handler : this.onEditAction
            },
            {
                itemId : 'toolDiagramEdit',
                tooltip : _SM.__language.GridBtn_Ttip_Edit_Diagram,
                type : 'diagramEdit',
                hidden : true,
                width : 20,
                scope : this,
                handler : this.onEditAction
            }
        ];

        this.myGrid.addTools(editTools);
        this.setEditMode(editMode);

    },

    setToolMode : function(myToolBt, bEdit){
        var myExtGrid = this.myGrid._extGrid;

        if (bEdit) {
            myExtGrid.down(myToolBt).show();
        } else {
            myExtGrid.down(myToolBt).hide();
        }
    },

    setEditMode : function(bEdit){

        var me = this, bRef, record, stRec, perms, myExtGrid;

        perms = _SM._UserInfo.perms[this.myMeta.viewCode] || [];
        myExtGrid = me.myGrid._extGrid;
        this.myGrid.editable = bEdit;

        if (!(perms['add'] || perms['change'] || perms['delete'])) {
            bRef = false;
        } else {
            var itemSelected = false;
            if (typeof me.myGrid.selected !== 'undefined') {
                itemSelected = me.myGrid.selected;
            }
            bRef = bEdit && itemSelected;
            if (bRef) {
                record = me.myGrid.selected;
                stRec = record.get('_ptStatus');
                bRef = !(stRec && stRec === _SM._ROW_ST.REFONLY);
            }

        }
        this.setEditToolBar(bEdit, bRef, perms);

    },

    setEditToolBar : function(bEdit, bRef, perms){

        var me = this;

        me.setToolMode('#toolFormAdd', bEdit && perms['add']);
        me.setToolMode('#toolFormUpd', bRef && perms['change']);

        me.setToolMode('#toolRowDel', bRef && perms['delete']);

        if (me.myMeta.viewCode === "prototype.Project" || me.myMeta.viewCode === "prototype.Diagram") {
            me.setToolMode('#toolDiagramEdit', bRef && perms['add']);
        }

        // DGT 
        var allowCopyRow = ( ! me.myMeta.denyCopyRow  ) && perms['add'] && bEdit; 
        me.setToolMode('#toolRowCopy', allowCopyRow );

        // Dont Delete
        // me.setToolMode('#toolMetaConfig', myExtGrid,  !bEdit );
        // me.setToolMode('#toolFormView', !(bRef && perms['change'] ));
    },

    // --------------------------------------------------------------------------

    onEditAction : function(ev, obj, head, btn){

        function doDelete(btn){
            if (btn === 'yes') {
                me.myGrid.deleteCurrentRecord();
            }
        }

        if (!this.formController) {
            this.formController = Ext.create('Softmachine.view.smform.FormController', {
                myMeta : this.myMeta
            });
        }

        this.myGrid.fireStartEdition(btn.itemId);

        // 'toolFormAdd', 'toolFormUpd', 'toolFormView', 'toolRowCopy', 'toolRowDel',
        switch (btn.itemId) {

        case 'toolRowDel':
            var me = this;
            Ext.MessageBox.confirm(_SM.__language.Title_Msg_Confirm_Delete,
                    _SM.__language.Msg_Confirm_Delete_Operation, doDelete);
            break;

        case 'toolFormAdd':

            // TODO: FIX: Add Mask to form load ( is not the right place )
            // showLoadingMask();
            // var delayedTask = new Ext.util.DelayedTask(function(args){
            // args.form.openNewForm(args.store);
            // });
            // delayedTask.delay(1, null, null, [{form: this.formController, store:
            // this.myGrid.store}]);


            // DGT 1604  TreeEdition requires currentRecord Default ( addChild )
            if ( this.myMeta.pciStyle == 'tree' ) {
                this.setTreeRef(); 

                // [] Borrar despues de probar 
                // this.myGrid.store.treeRef =  null 
                // var pNode; 

                // // Selected reg 
                // if ( this.myGrid.rowData ) {

                //     // TreeRef 
                //     var sm = this.myGrid._extGrid.getSelectionModel();
                //     pNode = sm.getSelection()[0]; 

                //     if ( ! pNode.isExpanded() ) {
                //         pNode.expand()
                //     }

                // }

                // var treeRef = { 
                //     'treeRefField' :this.myMeta.treeRefField, 
                //     'parentNode' : pNode 
                // }
                // this.myGrid.store.treeRef = treeRef;

            }

            this.formController.openNewForm(this.myGrid.store);
            break;

        case 'toolFormUpd':
            if (_SM.validaSelected(this.myGrid)) {
                var record = this.myGrid.selected; 
                if ( ! record.store ) { record.store = this.myGrid.store } 
                this.formController.openLinkedForm( record );
            }
            break;

        case 'toolFormView':
            if (_SM.validaSelected(this.myGrid)) {
                var record = this.myGrid.selected; 
                if ( ! record.store ) { record.store = this.myGrid.store } 
                this.formController.openLinkedForm(record, true);
            }
            break;

        case 'toolDiagramEdit':
            if (_SM.validaSelected(this.myGrid)) {
                Ext.getBody().mask('Loading...', 'loading');
                scriptLibrary = [];
                createJSFilesLibrary();
                var selectedItem = this.myGrid.rowData;
                loadJsFilesSequentially(scriptLibrary, 0, function(){
                    var win = Ext.create('ProtoUL.view.diagram.DiagramMainView');
                    if (selectedItem.project_id) {
                        win.setDiagramID(selectedItem.id);
                        win.setProjectID(selectedItem.project_id);
                    } else {
                        win.setProjectID(selectedItem.id);
                    }
                    win.show();
                    Ext.getBody().unmask();
                    win.maximize();
                });
            }
            break;

        case 'toolRowCopy':
            if ((!this.myGrid._extGrid ) || (!this.myGrid.editable )) {
                return;
            }

            if ( this.myMeta.pciStyle == 'tree' ) {
                this.copyTreeRecord();    
            } else {
                this.duplicateRecord();
            }; 
            
            break;

        }

        // Dont delete mask load ( form preview with mask?? )
        // function showLoadingMask()
        // {
        // loadText = 'Loading...';
        // //Use the mask function on the Ext.getBody() element to mask the body element during Ajax
        // calls
        // Ext.getBody().mask(loadText, 'loading');
        // Ext.Ajax.on('requestcomplete',Ext.getBody().unmask ,Ext.getBody());
        // Ext.Ajax.on('requestexception', Ext.getBody().unmask , Ext.getBody());
        // }
    },

    setTreeRef : function(){
        // Guarda en el store la informacion del nodo padre

        this.myGrid.store.treeRef =  null 
        var pNode; 

        // Selected reg 
        if ( this.myGrid.rowData ) {

            // TreeRef 
            var sm = this.myGrid._extGrid.getSelectionModel();
            pNode = sm.getSelection()[0]; 

            if ( ! pNode.isExpanded() ) {
                pNode.expand()
            }

        }

        var treeRef = { 
            'treeRefField' :this.myMeta.treeRefField, 
            'parentNode' : pNode 
        }
        this.myGrid.store.treeRef = treeRef;


    },

    copyTreeRecord : function(){

        // Obtiene y configura el zoom 
        var zoomModel  = _SM.getAutoTreeGridZoom( this.myMeta )
        var zoom = Ext.getCmp( 'toolZoom'); 

        zoom.initZoom( zoomModel )
        zoom.onZoomTriggerClick.call( zoom  ) 

    },

    doCopyTreeRecord : function( zoom, opts  ){

        // Marca el registo padre 
        var a = 1; 

    },


    duplicateRecord: function() {

        var rec = this.myGrid.selected;
        var nRec = _SM.copyFromRecord(this.myMeta, this.myGrid.store, rec ); 

        this.myGrid.store.add( nRec );

        if ( ! this.myGrid.store.autoSync  ) {
            _SM._doSyncMasterStore( this.myGrid.store );
        }

    },

});

_SM.validaSelected = function(myGrid){

    var myReg = myGrid.selected;

    if (!myReg) {
        _SM.errorMessage(_SM.__language.Title_Form_Panel, _SM.__language.GridAction_NoRecord);
        return false;
    }

    if (!myReg.store) {
        myReg.store = myGrid.store;
    }

    return true;
};