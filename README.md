# TMX2EA

TMX2EA converts Tiled format maps to EA installer format.

## How to use

Simply double click TMX2EA.exe and choose "Yes" to scan subfolders, and it will generate individual installers for each map as well as a master installer for all maps found.

If you only wish to update a single map you can either drag the .tmx directly onto TMX2EA or choose "No" when prompted and use the file selection dialog.

To use the installer, put

    ORG (some free space)
    #include "Path/To/Master Map Installer.event"

in your rom buildfile.

---

The Map Installer define the `SetChapterData()` macro, which is used to update the Chapter Data Editor with the appropriate properties.

These properties can be manually substituted in the generated event files, or defined as custom layer properties.

Supported Layer Properties:

| Name         | Default Value  | Notes                                                    |
| ------------ | -------------- | -------------------------------------------------------- |
| Main         |                | Required when there are multiple layers.                 |
| ChapterID    | ChapterID      | The chapter number/row in the chapter data editor.       |
| ObjectType1  | ObjectType     | The object set to use. Alias: ObjectType.                |
| ObjectType2  | 0              |                                                          |
| PaletteID    | PaletteID      | The palette to use.                                      |
| TileConfig   | TileConfig     | The tile configuration to use.                           |
| MapID        | map_id         | The index of the map in the Event Pointer Table.         |
| MapChangesID | map_changes    | The index of the map changes in the Event Pointer Table. |
| Anims1       | 0              | Tile Animation to use. Alias: Anims.                     |
| Anims2       | 0              |                                                          |

Required for tile change layers:

| Name         | Notes                                        |
| ------------ | -------------------------------------------- |
| ID           | Warning: the actual layer order matters too. |
| X            | X coordinate of the top left tile.           |
| Y            | Y coordinate of the top left tile.           |
| Height       | Height of the tile change.                   |
| Width        | Width of the tile change.                    |

Command line arguments:

	usage: tmx2ea [-h] [-s] [tmxpath [tmxpath ...]]

	positional arguments:
	  tmxpath            path to tmx file to process

	optional arguments:
	  -h, --help         show this help message and exit
	  -s, --scanfolders  scan all subfolders and generate master installer
