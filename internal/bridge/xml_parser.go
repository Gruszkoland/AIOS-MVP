package bridge

import (
	"encoding/xml"
	"io"
	"net/http"
)

// WholesaleProduct represents the B2B-Wholesale-Bridge schema v2.5
type WholesaleProduct struct {
	SKU            string  `xml:"id"`
	Name           string  `xml:"name"`
	WholesalePrice float64 `xml:"price_netto"`
	Stock          int     `xml:"qty"`
	Description    string  `xml:"desc"`
	Category       string  `xml:"cat"`
}

// DataProvider handles orchestration of multiple wholesale feeds
type DataProvider struct {
	Endpoints []string
}

// FetchWholesaleData parses XML from a provider URL (Concurrency-ready)
func (d *DataProvider) FetchWholesaleData(url string) ([]WholesaleProduct, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var data struct {
		Products []WholesaleProduct `xml:"product"`
	}

	if err := xml.Unmarshal(body, &data); err != nil {
		return nil, err
	}

	return data.Products, nil
}

// FilterHighMargin selects products with margin > 15% (ADRION Law)
func (d *DataProvider) FilterHighMargin(products []WholesaleProduct, retailPriceMap map[string]float64) []WholesaleProduct {
	var highMargin []WholesaleProduct
	for _, p := range products {
		retailPrice, exists := retailPriceMap[p.SKU]
		if exists {
			margin := (retailPrice - p.WholesalePrice) / retailPrice
			if margin > 0.15 {
				highMargin = append(highMargin, p)
			}
		}
	}
	return highMargin
}
