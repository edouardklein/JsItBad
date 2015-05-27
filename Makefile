README.md: doc/jsitbad.1.ronn
	sed 's/</`/g' < doc/jsitbad.1.ronn | sed 's/>/`/g'> README.md

doc: doc/jsitbad.1 doc/jsitbad.1.html

view_doc: doc/jsitbad.1.ronn
	ronn doc/jsitbad.1.ronn --man

doc/jsitbad.1: doc/jsitbad.1.ronn
	ronn doc/jsitbad.1.ronn 

doc/jsitbad.1.html: doc/jsitbad.1.ronn
	ronn doc/jsitbad.1.ronn --html

clean:
	rm doc/jsitbad.1 doc/jsitbad.1.html

