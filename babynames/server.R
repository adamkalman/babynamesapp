# server.R

library(shiny)
library(maps)
library(mapdata)

categories <- read.csv("dfForR.csv", header = TRUE)
states <- c('alabama','arkansas','arizona','california','colorado','connecticut','delaware','florida','georgia','iowa','idaho','illinois','indiana','kansas','kentucky','louisiana','mass','maryland','maine','michigan','minnesota','missouri','mississippi','montana','north carolina','north dakota','nebraska','new hampshire','new jersey','new mexico','nevada','new york','ohio','oklahoma','oregon','penn','rhode island','south carolina','south dakota','tenn','texas','utah','virginia','vermont','washington','wisconsin','west virginia','wyoming')
nicecolors <- colors()[c(142,562,553,258,91,99,368,624,207,8)]

shinyServer(function(input, output) {
  
  output$map <- renderPlot({
    
    catvector <- subset(categories, sex == input$gender & numclusters == input$numcategories)[['color']]
    colorAK <- nicecolors[catvector[1]+1]
    colorHI <- nicecolors[catvector[11]+1]
    catvector <- catvector[c(-1,-11)] + 1
    colorvector <- nicecolors[catvector]
    match <- match.map("state", states)
    
    layout(rbind(c(0,2,0,0,0,2), c(1,0,1,3,3,0), c(1,2,1,3,3,2)), heights=c(0.4, 0, .3), widths=c(0, 2, 0, 0, 1, 2))
    par(mar=rep(0, 4))
    par(oma=c(8,rep(0, 3)))
    layout.show(3)
    map("world2Hires", "USA:Alaska", fill = TRUE, col=colorAK)
    par(mar=rep(0, 4))
    map("state", boundary = FALSE, fill = TRUE, col = colorvector[match])
    par(mar=rep(0, 4))
    map("world2Hires", "Hawaii", fill = TRUE, col=colorHI)
    
  })
  
})
