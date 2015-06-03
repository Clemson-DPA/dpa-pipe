from dpa.ptask.area import PTaskArea
from dpa.ptask import PTask
from dpa.product.representation import ProductRepresentation
from dpa.maya.session import MayaSession


class ImportRef():

    choices = {}

    # -------------------------------------------------------------------------
    def __init__(self):
        self.ses = MayaSession().current()
        self.choices[""]=""

        self.ses.cmds.window(menuBar=True, title='Create Reference')
        self.ses.cmds.columnLayout()
        self.ses.cmds.optionMenu( 'sub', label='Sub', cc=self.setDir)
        self.ses.cmds.menuItem( label="")
        self.ses.cmds.textFieldGrp('dir', label='Dir', text ="", editable=False)
        self.ses.cmds.textFieldGrp('count', label='Count', text=1)
        self.ses.cmds.checkBox( 'group', label='Place Under Group?', value=0)
        self.ses.cmds.rowLayout(nc=1)
        self.ses.cmds.button(label="Import", width= 250, c=self.imp)

        self.populateSubs()

    def show(self):
        self.ses.cmds.showWindow()

    def imp( self, *args ):
        choose = self.ses.cmds.optionMenu('sub', query=True, value=True)
        path = self.ses.cmds.textFieldGrp('dir', query=True, text=True)
        count = int(self.ses.cmds.textFieldGrp('count', query=True, text=True))
        grp = int(self.ses.cmds.checkBox('group', query=True, value=True))
        if( path != "" ):
            for x in range(0, count):
                self.ses.cmds.file(path, r=1, gr=grp, gn="%s%s"%(choose,x), mergeNamespacesOnClash=1, namespace=":")
        else:
            print "Nothing selected"
        
    def setDir( self, *args ):
        self.ses.cmds.textFieldGrp('dir', edit=True, text='%s'%self.choices[args[0]])
        
    def populateSubs(self):
        
        ptask = self.ses.ptask
        
        for sub in ptask.latest_version.subscriptions:
            product = sub.product_version.product
            product_ver = sub.product_version
            
            product_rep_list = ProductRepresentation.list(product_version=product_ver.spec,type='ma', resolution='none')
            
            if( len(product_rep_list) == 1 ):
                product_rep = product_rep_list[0]
                
                choose = sub.product_version.product.name
                path = '%s/%s.%s'%(product_rep.directory, product.name, product_rep.type)
                
                self.choices[choose]=path
                self.ses.cmds.menuItem( label="%s"%choose )
    
    


