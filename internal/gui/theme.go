package gui

import (
	"image/color"
	
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/theme"
)

type fyneTheme struct{}

func (t *fyneTheme) Color(name fyne.ThemeColorName, variant fyne.ThemeVariant) color.Color {
	switch name {
	case theme.ColorNameBackground:
		if variant == theme.VariantLight {
			return color.NRGBA{R: 248, G: 248, B: 248, A: 255}
		}
		return color.NRGBA{R: 30, G: 30, B: 30, A: 255}
	case theme.ColorNameForeground:
		if variant == theme.VariantLight {
			return color.NRGBA{R: 50, G: 50, B: 50, A: 255}
		}
		return color.NRGBA{R: 220, G: 220, B: 220, A: 255}
	case theme.ColorNamePrimary:
		return color.NRGBA{R: 0, G: 180, B: 216, A: 255} // Fitbit teal
	case theme.ColorNameFocus:
		return color.NRGBA{R: 0, G: 180, B: 216, A: 100}
	}
	return theme.DefaultTheme().Color(name, variant)
}

func (t *fyneTheme) Font(style fyne.TextStyle) fyne.Resource {
	return theme.DefaultTheme().Font(style)
}

func (t *fyneTheme) Icon(name fyne.ThemeIconName) fyne.Resource {
	return theme.DefaultTheme().Icon(name)
}

func (t *fyneTheme) Size(name fyne.ThemeSizeName) float32 {
	switch name {
	case theme.SizeNamePadding:
		return 8
	case theme.SizeNameInlineIcon:
		return 20
	case theme.SizeNameScrollBar:
		return 16
	case theme.SizeNameText:
		return 14
	}
	return theme.DefaultTheme().Size(name)
}