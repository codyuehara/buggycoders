
(cl:in-package :asdf)

(defsystem "wall_avoider-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "ObstacleDistance" :depends-on ("_package_ObstacleDistance"))
    (:file "_package_ObstacleDistance" :depends-on ("_package"))
  ))