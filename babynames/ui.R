# ui.R

library(shiny)
library(maps)
library(mapdata)

shinyUI(fluidPage(
  titlePanel("Which states make similar baby name choices?"),
  
  sidebarLayout(
    sidebarPanel(
      
      radioButtons("gender", label = "",
                   choices = list("Boys" = "M", "Girls" = "F"), selected = "M"),
      
      sliderInput("numcategories", 
                  label = h4("Number of Groups"),
                  min = 2, max = 10, value = 5),
      
      helpText("The fifty states are grouped based on 2013 baby names. Informally, states of the same color will have similar kindergarten class lists in 2018.")
    ),
    
    mainPanel(plotOutput("map"))
  )
))