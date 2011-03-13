//
//  Configuration.h
//  Task Coach
//
//  Created by Jérôme Laheurte on 13/03/11.
//  Copyright 2011 __MyCompanyName__. All rights reserved.
//

#import <Foundation/Foundation.h>

#import "CDList.h"

/*
@interface TaskStatusSection : NSObject
{
    NSString *condition;
    BOOL displayed;
}

@property (nonatomic, readonly) NSString *condition;
@property (nonatomic) BOOL displayed;

@end
 */

@interface Configuration : NSObject
{
    NSURL *currentListURL;

    // NSArray *sections;
}

+ (Configuration *)instance;

- (void)save;

@property (copy) CDList *currentList;

// @property (nonatomic, copy) NSArray *sections;

@end