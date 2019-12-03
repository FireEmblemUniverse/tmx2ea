import six, tmx, sys, os, lzss, glob
import argparse

# TODO: Update macros, and don't overwrite existing maps

def showExceptionAndExit(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type, exc_value, tb)
    input("Press Enter key to exit.")
    sys.exit(-1)

def tmxTileToGbafeTile(tileGid):
    return ((tileGid - 1) * 4) if tileGid != 0 else 0

def makedmp(tmap, layer, fname):
    ary = [tmap.width+(tmap.height<<8)]

    for tile in layer.tiles:
        ary.append(tmxTileToGbafeTile(tile.gid))

    result = b''.join([(x).to_bytes(2,'little') for x in ary])

    with open(os.path.splitext(fname)[0]+"_data.dmp", 'wb') as myfile:
        lzss.compress(result, myfile)

def getTileChange(layer):
    tilemap = [tmxTileToGbafeTile(tile.gid) for tile in layer.tiles if tile.gid is not 0]

    result = layer.name.replace(" ", "_") + ":\nSHORT"

    for tile in tilemap:
        result += " ${:X}".format(tile)

    result += "\nALIGN 4\n\n"
    return result

def process(tmap, fname):
    """
    Let's see. Need to get layers. 
     <property name="Height" value ="3"/>
     <property name="ID" value ="1"/>
     <property name="Width" value ="3"/>
     <property name="X" value ="6"/>
     <property name="Y" value ="0"/>
    """

    output = ""

    chapterdata = "SetChapterData({ChapterID},{ObjectType},{ObjectType2},{PaletteID},{TileConfig},{MapID},Map,{Anims1},{Anims2},{MapChangesID})\nEventPointerTable({MapChangesID}, MapChanges)\n"
    macros = ""
    changes = ""

    #map properties
    ChapterID = "ChapterID"
    ObjectType = "ObjectType"
    ObjectType2 = "0"
    PaletteID = "PaletteID"
    TileConfig = "TileConfig"
    MapID = "map_id"
    Anims1 = "0"
    Anims2 = "0"
    MapChangesID = "map_changes"

    if (tmap.tilewidth == tmap.tileheight == 16)==False:
        print("WARNING:\n" + os.path.split(fname)[1] + " does not have 16x16 tiles, skipping")
        return None

    mainlayer = False    
    for layer in tmap.layers:
        isMain = False
        for p in layer.properties:
            name = p.name.lower()

            if name == "main":
                assert mainlayer==False, "More than one layer marked as Main in " + os.path.split(fname)[1]
                isMain = True
                mainlayer = True
                makedmp(tmap, layer, fname) # turn this layer into tiles and output a dmp

            elif name == "id":
                layerID = p.value

            elif name == "height":
                height = p.value

            elif name == "width":
                width = p.value

            elif name == "x":
                layerX = p.value

            elif name == "y":
                layerY = p.value

            elif name == "chapterid":
                ChapterID = p.value

            elif name == "objecttype1" or name == "objecttype":
                ObjectType = p.value

            elif name == "objecttype2":
                ObjectType2 = p.value                

            elif name == "paletteid":
                PaletteID = p.value

            elif name == "tileconfig":
                TileConfig = p.value

            elif name == "mapid":
                MapID = p.value

            elif name == "mapchangesid":
                MapChangesID = p.value

            elif name == "anims1" or name == "anims":
                Anims1 = p.value

            elif name == "anims2":
                Anims2 = p.value
            
        if len(tmap.layers)==1: # for the case of no properties and one layer
            mainlayer = True
            makedmp(tmap,layer,fname) # turn this layer into tiles and output a dmp
        
        if (isMain == False) and len(tmap.layers)!=1: # write any tile change layers
            macro = "TileMap(" + str(layerID) + "," + str(layerX) + "," + str(layerY) + "," + str(width) + "," + str(height) + "," + layer.name.replace(" ", "_") + ")\n"
            tileChangeData = getTileChange(layer)
            macros += macro
            changes += tileChangeData

    if mainlayer == False: #handle the case of no main and multiple layers
        print("WARNING:\n" + os.path.split(fname)[1] + " has no layer marked as Main, skipping")
        return None

    output += chapterdata.format(**locals())
    output += ("Map:\n#incbin \"" + os.path.splitext(os.path.split(fname)[1])[0]+"_data.dmp\"\n\nMapChanges:\n")

    if macros == "": #no map changes
        output = output.replace("EventPointerTable(map_changes, MapChanges)\n",'').replace("\nMapChanges:\n",'').replace("map_changes","0")

    else:
        output += (macros + "TileMapEnd\n\n" + changes)

    return output

def genHeaderLines():
    yield '#include "EAstdlib.event"\n\n'

    yield "#ifndef TMX2EA\n"
    yield "#define TMX2EA\n\n"

    yield "#ifndef ChapterDataTable\n"
    yield "    #ifdef _FE7_\n"
    yield "        #define ChapterDataTable 0xC9A200\n"
    yield "    #endif\n"
    yield "    #ifdef _FE8_\n"
    yield "        #define ChapterDataTable 0x8B0890\n"
    yield "    #endif\n"
    yield "#endif\n\n"

    yield '#define SetChapterData(ChapterID,ObjectType1,ObjectType2,PaletteID,TileConfig,MapID,MapPointer,Anims1,Anims2,MapChanges) "PUSH; ORG ChapterDataTable+(ChapterID*148)+4; BYTE ObjectType1 ObjectType2 PaletteID TileConfig MapID Anims1 Anims2 MapChanges; EventPointerTable(MapID,MapPointer); POP"\n\n'

    yield "#endif // TMX2EA\n\n"

def main():
    sys.excepthook = showExceptionAndExit
    createInstaller = False

    parser = argparse.ArgumentParser(description = 'Convert TMX file(s) to EA events. When no arguments are given, will ask what to do. If given a list of tmx files, will process them all. If given the `-s` option, will scan current directory for tmx files, process them all, and generate a master installer.')

    # input
    parser.add_argument("tmxFiles", nargs='*', help="path to tmx file(s) to process") #all arguments are tmx files
    parser.add_argument("-s", "--scanfolders", action="store_true", help="scan all subfolders and generate master installer") #optional scan

    # output
    parser.add_argument("-O", '--installer', help = 'output installer event (default: [Folder]/Master Map Installer.event)')
    
    # options
    parser.add_argument("-H", "--noheader", action="store_true", help="do not add in the tmx2ea header in generated file(s)")

    args = parser.parse_args()

    if (not args.tmxFiles) and (not args.scanfolders): #no arguments given and scanfolders is not true
        import tkinter as tk
        from tkinter import filedialog, messagebox

        root = tk.Tk()
        root.withdraw()

        if messagebox.askyesno("Folder Scan", "Scan all subfolders for .tmx files?"):
            args.scanfolders = True

        else:
            tmxFile = filedialog.askopenfilename(
                title = "Select TMX file to process",
                initialdir = os.getcwd(),
                filetypes = [
                    ("TMX files", ".tmx"),
                    ("All files", ".*")
                ]
            )
            
            if tmxFile == "":
                input("No file given.\nPress Enter key to exit.")
                sys.exit(-1)
            
            else:
                args.tmxFiles = [ tmxFile ]
    
    if args.scanfolders:
        args.tmxFiles = glob.glob('**/*.tmx',recursive=True)
        createInstaller = True

    processedFiles = []

    for tmxFile in args.tmxFiles:
        tmxMap = tmx.TileMap.load(tmxFile)
        dataLines = process(tmxMap, tmxFile)

        if dataLines:
            eventFile = os.path.splitext(tmxFile)[0]+".event"

            with open(eventFile, 'w') as f:
                f.write("// Map Data Installer Generated by tmx2ea\n\n")
                f.write('{\n\n')
                
                if not args.noheader:
                    f.writelines(genHeaderLines())

                f.write(dataLines)
                f.write('}\n')
            
            processedFiles.append(eventFile)

    if createInstaller:
        installerFile = args.installer if args.installer else "Master Map Installer.event"

        with open(installerFile, 'w') as f:
            f.writelines(map(lambda file: '#include "{}"\n'.format(os.path.relpath(file, os.path.dirname(installerFile))), processedFiles))

    input("....done!\nPress Enter key to exit.")

if __name__ == '__main__':
    main()
