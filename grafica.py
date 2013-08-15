"""
Programa adquicion datos
"""
import os
import pprint
import random
import sys
import wx

# The recommended way to use wx with mpl is with the WXAgg
# backend. 
#
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab

from escucha_com import SerialData as DataGen

class GraphFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Adquicion Datos'
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, size=(790,580), title=self.title)

        self.datagen = DataGen()
        
        self.datos = self.datagen.next()
        #self.data_a = [self.datos[0]]
        #self.data_b = [self.datos[1]]
        self.data_a = [0]
        self.data_b = [0]
        
        self.paused = 1
        
        self.datagen.envialo("stop")

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.bmp = wx.Bitmap("imas/fondo2_2.png")
        wx.FutureCall(50, self.make_canvas)
        wx.EVT_SIZE(self.panel, self.make_canvas)
        
        self.Timer1 = wx.Timer(self, id=2000)
        self.Bind(wx.EVT_TIMER, self.seg_pasados, self.Timer1)
        
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)        
        self.redraw_timer.Start(500)
        


    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
                
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        self.panel = wx.Panel(self)
        
        self.panel.SetFont(wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, 'ARIAL'))
                
        self.init_plot()
        
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        
        self.segundosp = 0
                
        #BOTON PLAY , style=wx.NO_BORDER
        bitmap=wx.Image("imas/play2.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.play_button = wx.BitmapButton(self.panel, -1, bitmap,
            pos=(23,422), size=(bitmap.GetWidth(), bitmap.GetHeight()))

        self.play_button.SetBitmapDisabled(wx.Image("imas/play2_dis.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.play_button.SetBitmapHover(wx.Image("imas/play2_hvr.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.Bind(wx.EVT_BUTTON, self.on_play_button, self.play_button)
        print self.play_button.GetMarginX()
        
        #BOTON STOP
        self.stop_button = wx.BitmapButton(self.panel, -1, bitmap=wx.Image("imas/stop2.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap(),
            pos=(72,422))
        self.stop_button.SetBitmapDisabled(wx.Image("imas/stop2_dis.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.stop_button.SetBitmapHover(wx.Image("imas/stop2_hvr.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.Bind(wx.EVT_BUTTON, self.on_stop_button, self.stop_button)
        self.stop_button.Enable(False)
        
        #BOTON UP
        self.up_button = wx.BitmapButton(self.panel, -1,bitmap=wx.Image("imas/up2.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap(),
        pos=(680,414))
        self.up_button.SetBitmapDisabled(wx.Image("imas/up2_dis.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.up_button.SetBitmapHover(wx.Image("imas/up2_hvr.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.Bind(wx.EVT_BUTTON, self.on_up_button, self.up_button)

        #BOTON DOWN
        self.down_button = wx.BitmapButton(self.panel, -1,bitmap=wx.Image("imas/down2.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap(), 
        pos=(727,431))
        self.down_button.SetBitmapDisabled(wx.Image("imas/down2_dis.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.down_button.SetBitmapHover(wx.Image("imas/down2_hvr.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.Bind(wx.EVT_BUTTON, self.on_down_button, self.down_button)
        
        #Valor MAX Kg
        self.maximo = wx.TextCtrl(self.panel, size=(12*5,-1), style=wx.TE_RIGHT, pos=(555,378))
        self.maximo.SetValue(str(max(self.data_b)))
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_maxkg, self.maximo)
        

        #valores actuales
        self.kg_now = wx.TextCtrl(self.panel, size=(12*5,-1), style=wx.TE_RIGHT, pos=(175,378))
        self.kg_now.SetValue(str(self.data_b[len(self.data_b) - 1]))
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_kgnow, self.kg_now)

        self.mm_now = wx.TextCtrl(self.panel, size=(12*5,-1), style=wx.TE_RIGHT, pos=(300,378))
        self.mm_now.SetValue(str(self.data_a[len(self.data_a) - 1]))
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_mmnow, self.mm_now)
        
        self.seg_now = wx.TextCtrl(self.panel, size=(12*5,-1), style=wx.TE_RIGHT, pos=(430,378))
        self.seg_now.SetValue(str(self.segundosp))
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_segnow, self.seg_now)  
        
        #self.hbox = wx.BoxSizer(wx.VERTICAL)
        #self.hbox.Add(self.canvas, 1, flag=wx.ALIGN_CENTER | wx.TOP | wx.GROW)
        #self.panel.SetSizer(self.hbox)
        #self.hbox.Fit(self)
        
    
    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((7.8, 3.3), facecolor=(1,1,1), dpi=self.dpi)
        

        self.axes = self.fig.add_subplot(111)
        #self.axes.set_axis_bgcolor('black')
        self.axes.set_title('Grafico Fuerza vs Desplazamiento', size=12)
        self.axes.set_xlabel('Desplazamiento [mm]', size=9)
        self.axes.set_ylabel('Fuerza [Kg]', size=9)

        
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        
        
        # plot the data as a line series, and save the reference 
        # to the plotted line series
        #
        self.plot_data = self.axes.plot(
            self.data_a, self.data_b, 
            linewidth=1,
            color=(0, 0, 0),
            )[0]

    def draw_plot(self):
        """ Redraws the plot
        """

        xmax = len(self.data_a) if len(self.data_a) > 10 else 10
        xmin = 0

        ymin = 0
        ymax = round(max(self.data_b), 0) + 1

        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)
                
        self.axes.grid(True, color='gray')

        # Using setp here is convenient, because get_xticklabels
        # returns a list over which one needs to explicitly 
        # iterate, and setp already handles this.
        #  
        #pylab.setp(self.axes.get_xticklabels(), 
        #    visible=self.cb_xlab.IsChecked())

        pylab.setp(self.axes.get_xticklabels(), visible=1)


        self.plot_data.set_xdata(np.arange(len(self.data_a)))
        self.plot_data.set_ydata(np.array(self.data_b))

        self.canvas.draw()
        
    
    def on_play_button(self, event):
        self.paused = 0
        self.Timer1.Start(1000)
        self.play_button.Enable(False)
        self.stop_button.Enable(True)
        self.up_button.Enable(False)
        self.down_button.Enable(False)
        print self.play_button.GetMarginX()
        
    def on_stop_button(self, event):
        self.paused = 1
        self.Timer1.Stop()
        self.play_button.Enable(True)
        self.stop_button.Enable(False)
        self.up_button.Enable(True)
        self.down_button.Enable(True)

    def on_up_button(self, event):
        self.datagen.envialo("sube")
        event.Skip()
        
    
    
    def on_down_button(self, event):
        self.datagen.envialo("baja")
        event.Skip()
    
        
    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
    
    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        #
        if not self.paused:
            self.data_a.append(self.datagen.next()[0])
            self.data_b.append(self.datagen.next()[1])
        self.draw_plot()
    
    def on_exit(self, event):
        self.Destroy()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')
		
    def on_update_maxkg(self, event):
        self.maximo.SetValue(str(max(self.data_b)))
		
    def on_update_kgnow(self, event):
        self.kg_now.SetValue(str(self.data_b[len(self.data_b)-1]))
	
    def on_update_mmnow(self, event):
        self.mm_now.SetValue(str(self.data_a[len(self.data_a)-1]))
	
    def seg_pasados(self,event):
        self.segundosp +=  1
    
    def on_update_segnow(self, event):
        self.seg_now.SetValue(str(self.segundosp))
        
    def make_canvas(self, event=None):
        # create the paint canvas
        dc = wx.ClientDC(self.panel)
        # forms a wall-papered background
        # formed from repeating image tiles
        brush_bmp = wx.BrushFromBitmap(self.bmp)
        dc.SetBrush(brush_bmp)
        # draw a rectangle to fill the canvas area
        w, h = self.GetClientSize()
        dc.DrawRectangle(0, 0, w, h)

        
        
if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = GraphFrame()
    app.frame.SetSizeHints(790, 580, maxW=790, maxH=580, incW=-1, incH=-1)
    app.frame.Show()
    app.MainLoop()
