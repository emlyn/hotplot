(defproject hotplot "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [[org.clojure/clojure "1.5.1"]
                 [congomongo "0.4.1"]
                 [compojure "1.1.5"]
                 [com.taoensso/timbre "2.3.0"]]
  :plugins [[lein-ring "0.8.2"]]

  :ring {:handler hotplot.core/app
         :port 5778})
