from PIL import Image, ImageFilter

# I can't get the effect to work directly in the kv file, so I will generate the slightly blurred images here and then save and reference them in the future.
image = Image.open('C:/Users/bensh/OneDrive/Essentials/Documents/Git/PROJECT/Final Design/graph reference.png')
blurredImage = image.filter(ImageFilter.GaussianBlur(10))

blurredIMage = 'C:/Users/bensh/OneDrive/Essentials/Documents/Git/PROJECT/Command Line VaR Programs Term 2/blurryGraph.png'
blurredImage.save(blurredIMage)
