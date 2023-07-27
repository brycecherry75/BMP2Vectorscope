import argparse, struct, sys, os, ctypes, BMPoperations

MaximumVectorscopeValue = 255 # for 24 bit BMP
MaximumHalfVectorscopeValue = MaximumVectorscopeValue / 2
VectorscopeFactor = 4 # MaximumVectorscopeValue multiplied by this value must not exceed 80% of TemplateResolution
CB_factor = ((MaximumHalfVectorscopeValue / (MaximumVectorscopeValue * 0.436))) * VectorscopeFactor
CR_factor = ((MaximumHalfVectorscopeValue / (MaximumVectorscopeValue * 0.615))) * VectorscopeFactor
TemplateResolution = 1280
HalfTemplateResolution = int(TemplateResolution / 2)
VectorscopeDrawColour = 10 # Green from Windows 16 colour palette
TemplateFilename = 'VectorscopeTemplate.bmp' # predrawn for speed

if __name__ == "__main__":
  parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
  parser.add_argument("--inputfile", help="BMP file input for conversion")
  parser.add_argument("--outputfile", help="BMP vectorgram file output")
  parser.add_argument("--line", type=int, default=-1, help="Single line to analyse (default: all)")

  ValidParameters = True
  BMP_Xresolution = 0
  BMP_Yresolution = 0

  args = parser.parse_args()
  if not args.inputfile:
    ValidParameters = False
    print("ERROR: BMP input file not specified")
  if not args.outputfile:
    ValidParameters = False
    print("ERROR: BMP output file not specified")

  BMP_SelectedLine = args.line

  if ValidParameters == True:
    BMPinputFile = args.inputfile
    if os.path.isfile(BMPinputFile):
      bmpfilesize = os.path.getsize(BMPinputFile)
      bmpbuffer = (ctypes.c_byte * bmpfilesize)()
      bmpfile = open(BMPinputFile, 'rb')
      bmpbuffer = bmpfile.read(bmpfilesize)
      ErrorCode = BMPoperations.CheckValidFormat(bmpbuffer)
      BMP_Xresolution = BMPoperations.ReadXresolution(bmpbuffer)
      BMP_Yresolution = BMPoperations.ReadYresolution(bmpbuffer)
      if ErrorCode != BMPoperations.ERROR_NONE:
        ValidParameters = False
        print("Error in", BMPinputFile, ", code", ErrorCode, "- refer to BMPoperations.py for definition")
      elif BMPoperations.ReadBitDepth(bmpbuffer) == 1:
        ValidParameters = False
        print("ERROR: Vectorscope representation is not possible on 1 bit per pixel images")
      elif BMP_SelectedLine < -1 or BMP_SelectedLine > (BMP_Xresolution - 1):
        ValidParameters = False
        print("ERROR: Manually selected line is not within 0 to", (BMP_Xresolution - 1))
      bmpfile.close()
    else:
      ValidParameters = False
      print("ERROR:", BMPinputFile, "not found")
    if os.path.isfile(TemplateFilename):
      bmpfilesize = os.path.getsize(TemplateFilename)
      bmpbuffer = (ctypes.c_byte * bmpfilesize)()
      bmpfile = open(TemplateFilename, 'rb')
      bmpbuffer = bmpfile.read(bmpfilesize)
      ErrorCode = BMPoperations.CheckValidFormat(bmpbuffer)
      Template_Xresolution = BMPoperations.ReadXresolution(bmpbuffer)
      Template_Yresolution = BMPoperations.ReadYresolution(bmpbuffer)
      if ErrorCode != BMPoperations.ERROR_NONE:
        ValidParameters = False
        print("Error in template file", TemplateFilename, ", code", ErrorCode, "- refer to BMPoperations.py for definition")
      elif Template_Xresolution != TemplateResolution or Template_Xresolution != TemplateResolution:
        ValidParameters = False
        print("ERROR: Template file", TemplateFilename, "does not have a square resoltion of", TemplateResolution, "pixels")
      elif BMPoperations.ReadBitDepth(bmpbuffer) != 4:
        ValidParameters = False
        print("ERROR: Template file", TemplateFilename, "is not 16 colour")
      bmpfile.close()
    else:
      ValidParameters = False
      print("ERROR: Template file", TemplateFilename, "not found")

  if ValidParameters == True:
    BMPinputFile = args.inputfile
    BMPoutputFile = args.outputfile
    bmpfilesize = os.path.getsize(BMPinputFile)
    bmpbuffer = (ctypes.c_byte * bmpfilesize)()
    bmpfile = open(BMPinputFile, 'rb')
    bmpbuffer = bmpfile.read(bmpfilesize)
    X_resolution = BMPoperations.ReadXresolution(bmpbuffer)
    Y_resolution = BMPoperations.ReadYresolution(bmpbuffer)
    BitDepth = BMPoperations.ReadBitDepth(bmpbuffer)
    Palette = (ctypes.c_byte * (256 * 3))()
    WithPalette = False
    templatefilesize = os.path.getsize(TemplateFilename)
    templatebuffer = (ctypes.c_byte * templatefilesize)()
    templatefile = open(TemplateFilename, 'rb')
    templatebuffer = templatefile.read(templatefilesize)
    VectorscopeBuffer = (ctypes.c_byte * templatefilesize)()
    for ByteToTransfer in range (templatefilesize):
      VectorscopeBuffer[ByteToTransfer] = templatebuffer[ByteToTransfer]
    templatefile.close()
    if BitDepth == 8 or BitDepth == 4:
      WithPalette = True
      BMPoperations.ReadPalette(Palette, bmpbuffer)
    for CurrentLine in range (BMP_Yresolution):
      if BMP_SelectedLine < 0 or BMP_SelectedLine == CurrentLine:
        # ensure a beam start from centre on a new line
        PreviousCB = HalfTemplateResolution
        PreviousCR = HalfTemplateResolution

        for CurrentHpixel in range(BMP_Xresolution):
          PixelValue = BMPoperations.ReadPixel(CurrentHpixel, CurrentLine, bmpbuffer)
          RED = 0
          GREEN = 0
          BLUE = 0
          if BitDepth == 24:
            SeparateRGBvalues = BMPoperations.SeparateRGBvalues_RGB888(PixelValue)
            RED = SeparateRGBvalues[0]
            GREEN = SeparateRGBvalues[1]
            BLUE = SeparateRGBvalues[2]
          elif BitDepth == 16:
            SeparateRGBvalues = BMPoperations.SeparateRGBvalues_RGB555(PixelValue)
            RED = SeparateRGBvalues[0]
            GREEN = SeparateRGBvalues[1]
            BLUE = SeparateRGBvalues[2]
          elif WithPalette == True:
            RED = Palette[(PixelValue * 3)]
            GREEN = Palette[(PixelValue * 3) + 1]
            BLUE = Palette[(PixelValue * 3) + 2]

          CB = int((0 - (RED * 0.147) - (GREEN * 0.289) + (BLUE * 0.436)) * CB_factor) + HalfTemplateResolution
          CR = HalfTemplateResolution - int((0 + (RED * 0.615) - (GREEN * 0.515) - (BLUE * 0.1)) * CR_factor)

          if CurrentHpixel == BMP_Xresolution: # ensure a beam return to centre on finishing the line
            PreviousCB = HalfTemplateResolution
            PreviousCR = HalfTemplateResolution

          BMPoperations.DrawLine(CB, CR, PreviousCB, PreviousCR, VectorscopeDrawColour, VectorscopeBuffer)
          PreviousCB = CB
          PreviousCR = CR

    bmpfile.close()

    vectorgramfile = open(BMPoutputFile, 'wb')
    vectorgramfile.write(VectorscopeBuffer)
    vectorgramfile.close()
    print("Vectorgram generation complete")