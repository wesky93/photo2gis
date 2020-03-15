import os
import tkinter as tk
from tkinter import filedialog, messagebox

import shapefile
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS


def get_decimal_coordinates(info):
    for key in ['Latitude', 'Longitude']:
        if 'GPS' + key in info and 'GPS' + key + 'Ref' in info:
            e = info['GPS' + key]
            ref = info['GPS' + key + 'Ref']
            result = (e[0][0] / e[0][1] +
                      e[1][0] / e[1][1] / 60 +
                      e[2][0] / e[2][1] / 3600
                      ) * (-1 if ref in ['S', 'W'] else 1)
            info[key] = result
    return info


def get_exif(filename):
    raw_exif = Image.open(filename)._getexif()
    exif = {}
    if raw_exif:
        exif = {TAGS.get(key, key): value for key, value in raw_exif.items()}
        if 'GPSInfo' in exif:
            gps_info = {GPSTAGS.get(key, key): value for key, value in exif['GPSInfo'].items()}
            exif['GPSInfo'] = get_decimal_coordinates(gps_info)

    return exif


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        self.dir = ''
        self.export_path = ''
        self.fails = []
        self.success = 0

        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.dir_lbl = tk.Label(self, width=40)
        self.dir_lbl.pack(side='top')
        self.dir_btn = tk.Button(root, text="폴더 선택", width=5, command=self.getDir)
        self.dir_btn.pack(side='top')

        self.start_btn = tk.Button(root, text="SHP 생성", width=10, command=self.makeShp)
        self.start_btn.grid(row=1, column=2)
        self.start_btn.pack(side='bottom')

    def getDir(self):
        self.dir = filedialog.askdirectory()
        self.export_path = os.path.join(self.dir, 'plants')
        self.dir_lbl.config(text=self.dir)

    def makeShp(self):
        print(self.dir)
        self.fails = []
        self.success = 0

        with shapefile.Writer(self.export_path, shapeType=shapefile.POINT,encoding="utf8") as shp:
            shp.field('file_path', 'C')
            shp.field('lat', 'C')
            shp.field('long', 'C')

            for data in self.getData():
                shp.record(data['file_path'], data['lat'], data['long'])
                shp.point(data["long"], data["lat"])

        with open(self.export_path+'.prj','w') as f:
            f.write('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]')
        self.finish()

    def getData(self):
        for x in self.getFiles():
            try:

                exif = get_exif(x)
                if gps := exif.get('GPSInfo'):
                    self.success += 1
                    yield {
                        "file_path": x,
                        "lat": gps.get('Latitude'),
                        "long": gps.get('Longitude'),
                    }
                else:
                    raise ValueError()
            except:
                self.fails.append(x)

    def finish(self):
        fails = '\n'.join(self.fails)
        messagebox.showinfo('작업 완료',
                            f"파일 경로 : {self.export_path}\n성공: {self.success}\n실패: {len(self.fails)}\n실패한 파일\n{fails}")

    def getFiles(self):
        for r, d, f in os.walk(self.dir):
            for file in f:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(r, file)
                    yield filepath


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
