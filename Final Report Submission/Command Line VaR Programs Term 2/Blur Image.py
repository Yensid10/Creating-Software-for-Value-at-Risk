from PIL import Image, ImageFilter

# I can't get the effect to work directly in the kv file, so I will generate the slightly blurred images here and then save and reference them in the future.
imageLocation = 'C:/Users/bensh/OneDrive/Essentials/Documents/Git/PROJECT/Command Line VaR Programs Term 2/Graph5.png'
image = Image.open(imageLocation)
blurredImage = image.filter(ImageFilter.GaussianBlur(10))

blurredIMage = imageLocation.replace('.png', 'Blurred.png')
blurredImage.save(blurredIMage)
